#!/usr/bin/env python3
"""Regenerate the generated regions of wiki/licenses.md and check the dependencies against license-policy.toml.

Usage, from the repository root:

    python3 -I wiki/_tools/gen_licenses.py                      # rewrite wiki/licenses.md in place
    python3 -I wiki/_tools/gen_licenses.py --check              # exit 1 on a policy violation or a stale licenses.md
    python3 -I wiki/_tools/gen_licenses.py --cache-dir DIR      # keep registry answers in DIR between runs
    python3 -I wiki/_tools/gen_licenses.py --list               # print every entry that is not allow as TSV

The script reads the lockfiles that `git ls-files` lists, asks the package registries
(PyPI, the npm registry, the Go module proxy) for each license, and runs `cargo metadata --locked`.
It needs network access and `cargo`.
It rules on every dependency and every `[[path]]` entry of `license-policy.toml` once,
and both the page and `--check` read those rulings.
`--check` prints one line per violation (verdict, lockfile, name, version, license, rule) to stdout.
A violation is a deny verdict, or a review verdict that no approved entry closes and no [scope] rule exempts.
Violations fail the check only while the policy says `status = "adopted"`.
In the repository it writes nothing except `wiki/licenses.md`, and `--list` writes nothing there.
Every temporary file lives in a system temporary directory.
`--cache-dir` must point outside the repository.
The hand-written scope notes come from `wiki/_tools/licenses-notes.tsv`.
Registry answers change over time, so `--check` can report drift without any change in the repository.
A cached answer is not fetched again, so run without `--cache-dir`, or empty it, to see that drift.
"""

from __future__ import annotations

import io
import re
import sys
import json
import time
import shutil
import fnmatch
import hashlib
import inspect
import tomllib
import zipfile
import argparse
import datetime
import tempfile
import subprocess
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple, NoReturn

POLICY_FILE = "license-policy.toml"
# Worst first. An `A AND B` takes the earlier of the two, an `A OR B` the later.
VERDICTS = ("deny", "review", "allow")
RANK = {v: i for i, v in enumerate(VERDICTS)}
STATUSES = ("proposed", "approved", "rejected")
# How `Policy.evaluate` reads each [expression] key. A policy that asks for another reading stops the run.
EXPRESSION_RULES = {"or": "best", "and": "worst", "with": "base-unless-deny", "slash": "or", "plus": "strip"}
# Lockfiles in these directories hold only CI dependencies, so their entries are `development` in [scope].
DEVELOPMENT_LOCKFILE_DIRS = (".github/actions/", ".depot/actions/")
# The outcome of one dependency. `exception` is an approved [[package]] or [[path]] entry.
# `exempt` is a review verdict that [scope] does not fail. The last two fail `--check`.
OUTCOMES = ("allow", "exception", "exempt", "review", "deny")
FAILING = ("review", "deny")
SPDX_TOKEN = re.compile(r"[A-Za-z0-9.\-]+\+?")
KEYWORDS = ("AND", "OR", "WITH")
PIP_CLASSIFIERS = {
    "mit license": "MIT",
    "mit no attribution license (mit-0)": "MIT-0",
    "apache software license": "Apache-2.0",
    "bsd license": "BSD",
    "isc license (iscl)": "ISC",
    "python software foundation license": "PSF-2.0",
    "public domain": "CC0-1.0",
    "the unlicense (unlicense)": "Unlicense",
    "boost software license 1.0 (bsl-1.0)": "BSL-1.0",
    "zlib/libpng license": "Zlib",
    "historical permission notice and disclaimer (hpnd)": "HPND",
    "universal permissive license (upl)": "UPL-1.0",
    "mozilla public license 1.1 (mpl 1.1)": "MPL-1.1",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "eclipse public license 1.0 (epl-1.0)": "EPL-1.0",
    "eclipse public license 2.0 (epl-2.0)": "EPL-2.0",
    "gnu general public license v2 (gplv2)": "GPL-2.0-only",
    "gnu general public license v2 or later (gplv2+)": "GPL-2.0-or-later",
    "gnu general public license v3 (gplv3)": "GPL-3.0-only",
    "gnu general public license v3 or later (gplv3+)": "GPL-3.0-or-later",
    "gnu lesser general public license v2 (lgplv2)": "LGPL-2.0-only",
    "gnu lesser general public license v2 or later (lgplv2+)": "LGPL-2.0-or-later",
    "gnu lesser general public license v3 (lgplv3)": "LGPL-3.0-only",
    "gnu lesser general public license v3 or later (lgplv3+)": "LGPL-3.0-or-later",
    "gnu affero general public license v3": "AGPL-3.0-only",
    "gnu affero general public license v3 or later (agplv3+)": "AGPL-3.0-or-later",
    "server side public license (sspl)": "SSPL-1.0",
}
# A pip `license` text that is not an SPDX expression is read as the SPDX id of the first pattern it starts with.
PIP_RAW = [
    (re.compile(r"(mit license\b|https?://(www\.)?opensource\.org/licenses/mit)", re.I), "MIT"),
    (re.compile(r"apache( software)? license,?( version| v)? ?2(\.0)?\b|apache 2\.0\b", re.I), "Apache-2.0"),
    (re.compile(r"3-clause bsd\b", re.I), "BSD-3-Clause"),
]
# PIP_RAW matches only the start of the text, and words after the name can take rights away
# ("Apache License 2.0 with Commons Clause"). A text with these words is not read as the bare name.
PIP_RAW_RESTRICTION = re.compile(r"proprietary|commons[ -]?clause|non-?commercial", re.I)
# The fields a [[package]] or [[path]] table can have besides its key fields. Any other field stops the run.
DECISION_FIELDS = frozenset(
    (
        "version",
        "license",
        "verdict",
        "reason",
        "status",
        "decided_by",
        "decided_on",
        "review_by",
        "proposed_on",
        "scope",
    )
)
LOCKFILE = re.compile(
    r"(^|/)(uv\.lock|pnpm-lock\.yaml|package-lock\.json|yarn\.lock|Cargo\.lock|go\.mod|go\.sum|requirements[^/]*\.txt)$"
)
GO_SIGNATURES = [
    ("MPL-2.0", r"Mozilla Public License,? (v\. |version )?2\.0"),
    ("GPL", r"GNU (LESSER |LIBRARY )?GENERAL PUBLIC"),
    ("Apache-2.0", r"Apache License,?\s+Version 2\.0"),
    ("MIT", r"Permission is hereby granted, free of charge"),
    ("BSD-3-Clause", r"Neither the name|names of (its|the copyright holder|their) contributors"),
    ("BSD-2-Clause", r"Redistribution and use in source and binary forms"),
    ("ISC", r"Permission to use, copy, modify, and(/or)? distribute this software for any"),
    ("Unlicense", r"free and unencumbered software"),
    ("CC0-1.0", r"CC0 1\.0"),
]
PIN = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)", re.M)
NOTES_HEADER = "path\tnote"
ECOSYSTEMS = ("pip", "npm", "cargo", "go")
TOP_PATHS = {"pip": "uv.lock", "npm": "pnpm-lock.yaml", "cargo": "rust/Cargo.lock"}
TOP_BASIS = {
    "pip": "패키지마다 `license_expression`(SPDX식), `License ::` 분류자, `license` 원문 중 처음으로 비어 있지 않은 값 하나",
    "npm": "레지스트리 `license` 필드",
    "cargo": "`Cargo.toml`의 `license` 필드",
    "go": "모듈 zip의 최상위 `LICENSE`·`COPYING` 본문 판별",
}
GO_SUM_NOTE = (
    "같은 디렉터리의 `go.mod` `require` 목록을 대신 썼다. `go.sum`은 검증용 해시 목록이고, "
    "빌드에 들어가지 않는 모듈(`/go.mod` 줄)까지 담는다"
)
GENERATED_NOTE = (
    "Generated from `wiki/_tools/gen_licenses.py`, `wiki/_tools/licenses-notes.tsv` and `license-policy.toml`"
    " — Do not edit by hand."
)
PIP_LABEL = {"E": "SPDX식", "C": "분류자", "R": "원문"}


class Entry(NamedTuple):
    name: str
    version: str
    license: str


class Lockfile(NamedTuple):
    path: str
    ecosystem: str
    counted: bool


class Ruling(NamedTuple):
    verdict: str
    rule: str


class Decision(NamedTuple):
    """One `[[package]]` or `[[path]]` table of the policy."""

    kind: str
    key: str
    ecosystem: str
    version: str
    license: str
    verdict: str
    status: str
    scope: str
    order: int
    problem: str

    @property
    def label(self) -> str:
        return f"[[{self.kind}]] `{self.key}`" + (f" {self.version}" if self.version else "")


class Judged(NamedTuple):
    outcome: str
    rule: str


class Finding(NamedTuple):
    outcome: str
    lockfile: str
    ecosystem: str
    name: str
    version: str
    license: str
    rule: str


def worst(a: Ruling, b: Ruling) -> Ruling:
    return a if RANK[a.verdict] <= RANK[b.verdict] else b


def best(a: Ruling, b: Ruling) -> Ruling:
    return a if RANK[a.verdict] >= RANK[b.verdict] else b


def expand_braces(glob: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", glob)
    if not m:
        return [glob]
    return [g for alt in m.group(1).split(",") for g in expand_braces(glob[: m.start()] + alt + glob[m.end() :])]


def glob_regex(glob: str) -> re.Pattern[str]:
    """Translate a `[[path]]` glob: `**/` is any number of directories, `*` and `?` stay inside one."""
    parts = []
    for alt in expand_braces(glob):
        out, i = [], 0
        while i < len(alt):
            if alt.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif alt.startswith("**", i):
                out.append(".*")
                i += 2
            elif alt[i] == "*":
                out.append("[^/]*")
                i += 1
            elif alt[i] == "?":
                out.append("[^/]")
                i += 1
            else:
                out.append(re.escape(alt[i]))
                i += 1
        parts.append("".join(out))
    return re.compile(r"(?:" + "|".join(parts) + r")\Z")


def pip_name(name: str) -> str:
    """Return the PEP 503 form: `requirements.txt` keeps the author's spelling, `uv.lock` does not."""
    return re.sub(r"[-_.]+", "-", name).lower()


def iso_date(value: object, where: str) -> str:
    """Return a `review_by` value as YYYY-MM-DD, because the check compares dates as strings."""
    if isinstance(value, datetime.datetime):
        value = value.date()
    if isinstance(value, datetime.date):
        return value.isoformat()
    try:
        return datetime.date.fromisoformat(str(value)).isoformat()
    except ValueError:
        sys.exit(f"{POLICY_FILE}: {where} review_by {value!r}; expected YYYY-MM-DD")


def is_error(lic: str) -> bool:
    return lic.startswith(("ERR ", "R:ERR "))


def found_expression(eco: str, lic: str) -> str | None:
    """Return the SPDX expression a collected license string stands for, or None when it names none."""
    if is_error(lic):
        return None
    if eco == "cargo" and lic.startswith("FILE:"):
        return None
    if eco != "pip":
        return lic
    kind, _, val = lic.partition(":")
    if kind == "E":
        return val
    if kind == "C":
        # Several classifiers on one package must all hold, as in an `AND`.
        parts = [p for p in val.split(";") if p not in ("OSI Approved", "DFSG approved")]
        ids = [PIP_CLASSIFIERS.get(p.lower()) for p in parts]
        if not ids or None in ids:
            return None
        return " AND ".join(dict.fromkeys(i for i in ids if i))
    text = " ".join(val.split())
    if not PIP_RAW_RESTRICTION.search(text):
        for pattern, spdx in PIP_RAW:
            if pattern.match(text):
                return spdx
    return PIP_CLASSIFIERS.get(text.lower(), text) or None


class Policy:
    """`license-policy.toml`, read with `tomllib` and checked against what this script implements."""

    def __init__(self, data: dict[str, Any], today: str) -> None:
        def fail(message: str) -> NoReturn:
            sys.exit(f"{POLICY_FILE}: {message}")

        if data.get("schema") != 1:
            fail(f"schema {data.get('schema')!r}; gen_licenses.py reads schema 1")
        self.status = data.get("status")
        if self.status not in ("draft", "adopted"):
            fail(f"status {self.status!r}; expected draft or adopted")
        self.review_by = iso_date(data["review_by"], "policy") if data.get("review_by") else ""
        expression = data.get("expression", {})
        for key, want in EXPRESSION_RULES.items():
            if expression.get(key) != want:
                fail(f"[expression] {key} = {expression.get(key)!r}; gen_licenses.py implements {want!r}")
        self.alias = {k.lower(): v for k, v in expression.get("alias", {}).items()}
        self.allow = list(data.get("allow", {}).get("licenses", []))
        self.exact: dict[str, dict[str, str]] = {}
        self.prefixes: dict[str, list[str]] = {}
        seen: dict[str, str] = {}
        for verdict in ("allow", "deny", "review"):
            table = data.get(verdict, {})
            self.exact[verdict] = {x.lower(): x for x in table.get("licenses", [])}
            self.prefixes[verdict] = list(table.get("prefixes", []))
            for x in self.exact[verdict]:
                if x in seen:
                    fail(f"`{x}` is in both [{seen[x]}] and [{verdict}]")
                seen[x] = verdict
        if self.prefixes["allow"]:
            fail("[allow] prefixes is not read; list the identifiers")
        self.scope: dict[str, dict[str, str]] = {}
        for name, rules in data.get("scope", {}).items():
            if not isinstance(rules, dict) or set(rules) != {"deny", "review"}:
                fail(f"[scope] {name} needs exactly `deny` and `review`")
            if any(v not in ("fail", "exempt") for v in rules.values()):
                fail(f"[scope] {name}: each rule is fail or exempt")
            self.scope[name] = rules
        if "distributed" not in self.scope:
            fail("[scope] distributed is missing")
        self.require_one_of = list(data.get("approval", {}).get("require_one_of", []))
        self.packages = [self._decision("package", i, t, today) for i, t in enumerate(data.get("package", []))]
        self.paths = [self._decision("path", i, t, today) for i, t in enumerate(data.get("path", []))]

    def _decision(self, kind: str, index: int, table: dict[str, Any], today: str) -> Decision:
        key_field = "name" if kind == "package" else "glob"
        required = [key_field, "reason", "status"] + (["ecosystem"] if kind == "package" else [])
        where = f"[[{kind}]] #{index + 1} ({table.get(key_field, '?')})"
        for field in required:
            if not table.get(field):
                sys.exit(f"{POLICY_FILE}: {where} has no `{field}`")
        unknown = sorted(set(table) - DECISION_FIELDS - {key_field, *required})
        if unknown:
            sys.exit(f"{POLICY_FILE}: {where} has unknown fields {unknown}")
        if kind == "package" and table["ecosystem"] not in ECOSYSTEMS:
            sys.exit(f"{POLICY_FILE}: {where} ecosystem {table['ecosystem']!r}; expected one of {ECOSYSTEMS}")
        if table["status"] not in STATUSES:
            sys.exit(f"{POLICY_FILE}: {where} status {table['status']!r}; expected one of {STATUSES}")
        if table.get("verdict", "") not in ("", *VERDICTS):
            sys.exit(f"{POLICY_FILE}: {where} verdict {table['verdict']!r}; expected one of {VERDICTS}")
        if table.get("scope", "") not in ("", *self.scope):
            sys.exit(f"{POLICY_FILE}: {where} scope {table['scope']!r}; [scope] has {tuple(self.scope)}")
        review_by = iso_date(table["review_by"], where) if table.get("review_by") else ""
        problem = ""
        if table["status"] == "approved":
            # A [[path]] matches by glob alone, so a version there pins nothing and cannot stand in for review_by.
            fields = [f for f in self.require_one_of if kind == "package" or f != "version"]
            if not any(table.get(f) for f in fields):
                problem = f"approved without {' or '.join(fields)} ([approval])"
            elif review_by and review_by < today:
                problem = f"approval expired on {review_by}"
        key = table[key_field]
        return Decision(
            kind=kind,
            key=pip_name(key) if table.get("ecosystem") == "pip" else key,
            ecosystem=table.get("ecosystem", ""),
            version=str(table.get("version", "")),
            license=table.get("license", ""),
            verdict=table.get("verdict", ""),
            status=table["status"],
            scope=table.get("scope", ""),
            order=index,
            problem=problem,
        )

    def id_ruling(self, ident: str) -> Ruling:
        ident = self.alias.get(ident.lower(), ident)
        # A bare id outside SPDX also meets the `LicenseRef-` entries, so `Commons-Clause` is `LicenseRef-Commons-Clause`.
        # Only the exact lists and the deny prefixes see that form: the review prefix `LicenseRef-` would catch every unknown id.
        names = [ident] if ident.lower().startswith("licenseref-") else [ident, "LicenseRef-" + ident]
        for name in names:
            for verdict in ("allow", "deny", "review"):
                if name.lower() in self.exact[verdict]:
                    return Ruling(verdict, f"[{verdict}] licenses `{self.exact[verdict][name.lower()]}`")
        for verdict, candidates in (("deny", names), ("review", names[:1])):
            for name in candidates:
                for prefix in self.prefixes[verdict]:
                    if name.lower().startswith(prefix.lower()):
                        return Ruling(verdict, f"[{verdict}] prefixes `{prefix}`")
        return Ruling("review", f"`{ident}` is in no list")

    def evaluate(self, expr: str | None) -> Ruling:
        """Rule on an SPDX expression. Anything that does not parse is review."""
        not_spdx = Ruling("review", "not an SPDX expression")
        if not expr or not expr.strip():
            return not_spdx
        toks = re.findall(r"\(|\)|[^\s()]+", expr.replace("/", " OR "))
        pos = 0

        def peek() -> str:
            return toks[pos].upper() if pos < len(toks) else ""

        def ident() -> str:
            nonlocal pos
            tok = toks[pos] if pos < len(toks) else ""
            if tok.upper() in KEYWORDS or not SPDX_TOKEN.fullmatch(tok):
                raise ValueError(tok)
            pos += 1
            return tok

        def atom() -> Ruling:
            nonlocal pos
            if peek() == "(":
                pos += 1
                ruling = orx()
                if peek() != ")":
                    raise ValueError("(")
                pos += 1
                return ruling
            ruling = self.id_ruling(ident().removesuffix("+"))
            if peek() == "WITH":
                pos += 1
                exception = ident()
                # An exception may only widen the license, so it changes nothing unless the policy denies it.
                denied = self.id_ruling(exception)
                if denied.verdict == "deny":
                    ruling = Ruling("deny", f"{denied.rule} after `WITH`")
            return ruling

        def andx() -> Ruling:
            nonlocal pos
            ruling = atom()
            while peek() == "AND":
                pos += 1
                ruling = worst(ruling, atom())
            return ruling

        def orx() -> Ruling:
            nonlocal pos
            ruling = andx()
            while peek() == "OR":
                pos += 1
                ruling = best(ruling, andx())
            return ruling

        try:
            ruling = orx()
        except ValueError:
            return not_spdx
        return ruling if pos == len(toks) else not_spdx

    def decision_for(self, eco: str, name: str, version: str) -> Decision | None:
        """Return the [[package]] entry for a dependency: a pinned version first, then an exact name."""
        if eco == "pip":
            name = pip_name(name)
        hits = [
            d
            for d in self.packages
            if d.ecosystem == eco and fnmatch.fnmatchcase(name, d.key) and d.version in ("", version)
        ]
        return min(hits, key=lambda d: (d.version == "", d.key != name, d.order), default=None)

    def judge(self, found: Ruling, decision: Decision | None, scope: str) -> Judged:
        """Apply an entry and the scope to the verdict of the license that was found."""
        verdict, rule = found
        if decision is not None and decision.status == "rejected":
            verdict, rule = "deny", f"{decision.label} status=rejected"
        elif decision is not None and (decision.status == "proposed" or decision.problem):
            # Only an approved entry changes the license, the verdict or the scope.
            why = decision.problem or "status=proposed"
            if found.verdict == "deny":
                rule = f"{found.rule}; {decision.label} {why}"
            else:
                verdict, rule = "review", f"{decision.label} {why}"
        elif decision is not None:
            scope = decision.scope or scope
            if decision.verdict:
                verdict, rule = decision.verdict, f"{decision.label} verdict={decision.verdict}"
            elif decision.license:
                verdict, rule = self.evaluate(decision.license)
                rule = f"{decision.label} license=`{decision.license}`: {rule}"
            if verdict != "deny" and decision.verdict != "review":
                return Judged("exception", f"{decision.label} status=approved")
        if verdict != "allow" and self.scope.get(scope, self.scope["distributed"])[verdict] == "exempt":
            return Judged("exempt", f"{rule}; [scope] {scope} exempts {verdict}")
        return Judged(verdict, rule)


def load_policy(root: Path, today: str) -> Policy:
    path = root / POLICY_FILE
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as e:
        sys.exit(f"{POLICY_FILE}: {e}")
    return Policy(data, today)


def lockfile_scope(path: str) -> str:
    return "development" if path.startswith(DEVELOPMENT_LOCKFILE_DIRS) else "distributed"


def judge_all(policy: Policy, files: list[Lockfile], data: dict[str, list[Entry]], tracked: list[str]) -> list[Finding]:
    """Rule on every collected dependency and every `[[path]]` entry. The page and `--check` both read this."""
    eco_of = {f.path: f.ecosystem for f in files}
    findings = []
    applied: set[int] = set()
    for path, entries in data.items():
        eco = eco_of[path]
        for e in entries:
            found = policy.evaluate(found_expression(eco, e.license))
            decision = policy.decision_for(eco, e.name, e.version)
            if decision is not None:
                applied.add(decision.order)
            judged = policy.judge(found, decision, lockfile_scope(path))
            findings.append(Finding(judged.outcome, path, eco, e.name, e.version, e.license, judged.rule))
    for d in policy.packages:
        if d.order not in applied:
            print(f"warning: {d.label} applies to no dependency", file=sys.stderr)  # noqa: T201
    for d in policy.paths:
        pattern = glob_regex(d.key)
        matched = sum(1 for p in tracked if pattern.match(p))
        if not matched:
            print(f"warning: {d.label} matches no tracked file", file=sys.stderr)  # noqa: T201
            continue
        judged = policy.judge(policy.evaluate(d.license), d, "distributed")
        findings.append(Finding(judged.outcome, f"추적 파일 {matched}개", "path", d.key, "", d.license, judged.rule))
    return findings


class Cache:
    """Registry answers kept as one JSON file per ecosystem. Errors are never stored.

    Each file carries the `tag` of the lookup code that wrote it. A file with another tag is ignored,
    so a change to a fetch function (or a revert of one) cannot hide behind answers the old code gave.
    """

    def __init__(self, directory: Path | None, tag: str) -> None:
        self.directory = directory
        self.tag = tag
        self.data: dict[str, dict[str, str]] = {}

    def _file(self, eco: str) -> Path | None:
        return self.directory / f"{eco}.json" if self.directory else None

    def load(self, eco: str) -> dict[str, str]:
        if eco not in self.data:
            f = self._file(eco)
            stored: object = {}
            if f and f.exists():
                try:
                    stored = json.loads(f.read_text())
                except json.JSONDecodeError:
                    print(f"warning: {f} is not valid JSON; asking the registry again", file=sys.stderr)  # noqa: T201
            if isinstance(stored, dict) and stored.get("tag") == self.tag:
                self.data[eco] = stored.get("answers", {})
            else:
                self.data[eco] = {}
        return self.data[eco]

    def save(self, eco: str) -> None:
        f = self._file(eco)
        if f:
            f.parent.mkdir(parents=True, exist_ok=True)
            # Write a sibling file and rename it, so an interrupted run never leaves half a JSON file.
            tmp = f.with_name(f.name + ".tmp")
            tmp.write_text(json.dumps({"tag": self.tag, "answers": self.data[eco]}, sort_keys=True))
            tmp.replace(f)


def lookup_all(
    eco: str, keys: list[tuple[str, str]], fetch: Callable[[str, str], str], workers: int, cache: Cache
) -> dict[tuple[str, str], str]:
    """Return {(name, version): license}. Failures (see `is_error`) are returned but not cached."""
    known = cache.load(eco)
    todo = [k for k in keys if f"{k[0]}\t{k[1]}" not in known]
    fresh: dict[tuple[str, str], str] = {}
    if todo:
        with ThreadPoolExecutor(workers) as ex:
            for k, lic in zip(todo, ex.map(lambda k: fetch(*k), todo)):
                fresh[k] = lic
                if not is_error(lic):
                    known[f"{k[0]}\t{k[1]}"] = lic
        cache.save(eco)
    return {k: fresh[k] if k in fresh else known[f"{k[0]}\t{k[1]}"] for k in keys}


def http_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.load(resp)


def fetch_pip(name: str, version: str) -> str:
    # A local version label (`2.9.1+cpu`) marks a build from another index. PyPI only knows the public version.
    public_version = version.split("+", 1)[0]
    try:
        d = http_json(f"https://pypi.org/pypi/{name}/{public_version}/json")["info"]
    except Exception as e:  # noqa: BLE001 - any failure is a reported "unknown" license
        return "R:ERR " + str(e)[:40]
    classifiers = [c.split(" :: ")[-1] for c in d.get("classifiers", []) if c.startswith("License ::")]
    raw = " ".join((d.get("license") or "").split())[:80]
    if d.get("license_expression"):
        return "E:" + d["license_expression"]
    if classifiers:
        return "C:" + ";".join(classifiers)
    return "R:" + raw


def fetch_npm(name: str, version: str) -> str:
    err = ""
    for attempt in range(3):
        if attempt:
            time.sleep(2**attempt)
        try:
            d = http_json(f"https://registry.npmjs.org/{name.replace('/', '%2F')}/{version}")
            lic = d.get("license") or d.get("licenses")
            if isinstance(lic, dict):
                lic = lic.get("type")
            if isinstance(lic, list):
                lic = " OR ".join(x.get("type", "?") if isinstance(x, dict) else str(x) for x in lic)
            return str(lic) if lic else "UNKNOWN"
        except urllib.error.HTTPError as e:
            err = str(e)[:40]
            if e.code == 404:
                break
        except Exception as e:  # noqa: BLE001
            err = str(e)[:40]
    return "ERR " + err


def go_escape(s: str) -> str:
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), s)


def fetch_go(module: str, version: str) -> str:
    try:
        url = f"https://proxy.golang.org/{go_escape(module)}/@v/{go_escape(version)}.zip"
        with urllib.request.urlopen(url, timeout=120) as resp:
            z = zipfile.ZipFile(io.BytesIO(resp.read()))
        root = f"{module}@{version}/"
        files = [
            n
            for n in z.namelist()
            if n.startswith(root)
            and "/" not in n[len(root) :]
            and re.match(r"(LICEN[CS]E|COPYING)", n[len(root) :], re.I)
        ]
        found = []
        for f in files:
            txt = z.read(f).decode("utf-8", "replace")
            for label, pat in GO_SIGNATURES:
                if re.search(pat, txt, re.I):
                    found.append(label)
                    break
            else:
                found.append("UNKNOWN(" + f[len(root) :] + ")")
        return " AND ".join(sorted(set(found))) or "NO-LICENSE-FILE"
    except Exception as e:  # noqa: BLE001
        return "ERR " + str(e)[:40]


def fetch_tag() -> str:
    """Return a hash of the code that turns a registry answer into a license string, for `Cache`."""
    code = (http_json, fetch_pip, fetch_npm, go_escape, fetch_go)
    source = "".join(inspect.getsource(f) for f in code) + repr(GO_SIGNATURES)
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def go_requires(text: str) -> list[tuple[str, str]]:
    """Return (module, version) for each `require` entry in a go.mod, single-line or in a block."""
    keys: list[tuple[str, str]] = []
    in_block = False
    for raw in text.splitlines():
        fields = raw.split("//", 1)[0].split()
        if in_block:
            if fields == [")"]:
                in_block = False
                continue
        elif fields[:1] == ["require"]:
            fields = fields[1:]
            if fields == ["("]:
                in_block = True
                continue
        else:
            continue
        if len(fields) == 2:
            keys.append((fields[0].strip('"'), fields[1]))
    return keys


def npm_keys(path: Path) -> list[tuple[str, str]]:
    text = path.read_text()
    if path.name.endswith(".json"):
        # An npm alias (`node_modules/string-width-cjs`) installs the package that `name` gives.
        keys = {
            (v.get("name") or k.rsplit("node_modules/", 1)[1], v["version"])
            for k, v in json.loads(text)["packages"].items()
            if "node_modules/" in k and "version" in v and not v.get("link")
        }
    else:
        if "\npackages:\n" not in text:
            return []
        section = text.split("\npackages:\n", 1)[1].split("\nsnapshots:\n", 1)[0]
        keys = set(re.findall(r"^  '?/?((?:@[^/@']+/)?[^@/'\s]+)[@/]([0-9][^':\s_(]*)[^:]*'?:\s*$", section, re.M))
    return sorted(keys)


def git_files(root: Path) -> list[str]:
    # Without -z, git quotes a path with non-ASCII bytes ("\"a/\\352\\260\\200.png\""), and no [[path]] glob matches it.
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def describe(root: Path, path: str) -> Lockfile:
    name = Path(path).name
    if name == "uv.lock":
        return Lockfile(path, "pip", True)
    if name.startswith("requirements"):
        return Lockfile(path, "pip", bool(PIN.search((root / path).read_text())))
    if name in ("pnpm-lock.yaml", "package-lock.json"):
        return Lockfile(path, "npm", True)
    if name == "Cargo.lock":
        return Lockfile(path, "cargo", True)
    if name == "go.mod":
        return Lockfile(path, "go", True)
    if name == "go.sum":
        return Lockfile(path, "go", False)
    sys.exit(f"{path}: no rule for this lockfile type; teach gen_licenses.py about it")


def collect(root: Path, files: list[Lockfile], cache: Cache) -> dict[str, list[Entry]]:
    """Return {path: [Entry, ...]} for every counted lockfile."""
    result: dict[str, list[Entry]] = {}
    counted = [f for f in files if f.counted]

    pip_keys: dict[str, list[tuple[str, str]]] = {}
    for f in counted:
        if f.ecosystem != "pip":
            continue
        if f.path.endswith("uv.lock"):
            lock = tomllib.loads((root / f.path).read_text())
            pip_keys[f.path] = [
                (p["name"], p["version"]) for p in lock["package"] if p.get("source", {}).get("registry")
            ]
        else:
            pip_keys[f.path] = PIN.findall((root / f.path).read_text())
    pip_all = sorted({k for ks in pip_keys.values() for k in ks})
    pip_lic = lookup_all("pip", pip_all, fetch_pip, 16, cache)
    for path, ks in pip_keys.items():
        result[path] = [Entry(n, v, pip_lic[(n, v)]) for n, v in ks]

    npm_by_file = {f.path: npm_keys(root / f.path) for f in counted if f.ecosystem == "npm"}
    npm_all = sorted({k for ks in npm_by_file.values() for k in ks})
    npm_lic = lookup_all("npm", npm_all, fetch_npm, 32, cache)
    for path, ks in npm_by_file.items():
        result[path] = [Entry(n, v, npm_lic[(n, v)]) for n, v in ks]

    for f in counted:
        if f.ecosystem != "cargo":
            continue
        manifest = root / Path(f.path).parent / "Cargo.toml"
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                ["cargo", "metadata", "--manifest-path", str(manifest), "--format-version", "1", "--locked"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
        if proc.returncode != 0:
            sys.exit(f"cargo metadata failed for {f.path}:\n{proc.stderr[-800:]}")
        packages = json.loads(proc.stdout)["packages"]
        result[f.path] = [
            Entry(p["name"], p["version"], p.get("license") or "FILE:" + (p.get("license_file") or ""))
            for p in packages
            if p.get("source") is not None
        ]

    go_by_file: dict[str, list[tuple[str, str]]] = {}
    for f in counted:
        if f.ecosystem == "go":
            go_by_file[f.path] = go_requires((root / f.path).read_text())
    go_all = sorted({k for ks in go_by_file.values() for k in ks})
    go_lic = lookup_all("go", go_all, fetch_go, 8, cache)
    for path, ks in go_by_file.items():
        result[path] = [Entry(m, v, go_lic[(m, v)]) for m, v in ks]
    return result


def load_notes(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != NOTES_HEADER:
        sys.exit(f"{path}: first line must be {NOTES_HEADER!r}")
    notes: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) != 2:
            sys.exit(f"{path}: expected 2 tab-separated columns: {line!r}")
        if cols[0] in notes:
            sys.exit(f"{path}: duplicate row for {cols[0]!r}")
        notes[cols[0]] = cols[1]
    return notes


def short_path(path: str) -> str:
    parts = path.split("/")
    return path if len(parts) <= 5 else f"{parts[0]}/.../{'/'.join(parts[-2:])}"


def render_scope(files: list[Lockfile], notes: dict[str, str]) -> str:
    present = {f.path: f for f in files}
    ordered = [p for p in notes if p in present] + [p for p in present if p not in notes]
    rows = []
    sums = [p for p in ordered if present[p].path.endswith("go.sum")]
    for p in ordered:
        f = present[p]
        if p in sums:
            continue
        action = "집계" if f.counted else "제외"
        note = notes.get(p, "미확인")
        rows.append(f"| `{p}` | {f.ecosystem} | {action} | {note} |".replace("|  |", "| |"))
    if sums:
        names = ", ".join(f"`{p}`" for p in sums)
        rows.append(f"| {names} | go | 제외 | {GO_SUM_NOTE} |")
    counted = sum(f.counted for f in files)
    reqs = sum(1 for f in files if not f.counted and Path(f.path).name.startswith("requirements"))
    excluded = [f"`requirements.txt` {reqs}개"] if reqs else []
    if sums:
        excluded.append(f"`go.sum` {len(sums)}개")
    absent = "" if any(Path(f.path).name == "yarn.lock" for f in files) else " `yarn.lock`은 없다."
    return "\n".join(
        [
            GENERATED_NOTE,
            "",
            f"`git ls-files | grep -E '{LOCKFILE.pattern}'`는 {len(files)}개 파일을 낸다.{absent}",
            "",
            "| 파일 | 생태계 | 처리 | 비고 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            f"합계: 집계 {counted}개, 제외 {len(files) - counted}개({', '.join(excluded)}).",
        ]
    )


def md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_summary(files: list[Lockfile], notes: dict[str, str], findings: list[Finding]) -> str:
    counted = [f.path for f in files if f.counted]
    order = [p for p in notes if p in counted] + [p for p in counted if p not in notes]
    eco_of = {f.path: f.ecosystem for f in files}
    by_file: dict[str, Counter[str]] = {p: Counter() for p in order}
    paths: Counter[str] = Counter()
    for f in findings:
        (paths if f.ecosystem == "path" else by_file[f.lockfile])[f.outcome] += 1
    rows = []
    for p in order:
        c = by_file[p]
        cells = " | ".join(str(c[o]) for o in OUTCOMES)
        rows.append(f"| `{short_path(p)}` | {eco_of[p]} | {sum(c.values())} | {cells} |")
    cells = " | ".join(str(paths[o]) for o in OUTCOMES)
    rows.append(f"| 잠금 파일 밖 파일(`[[path]]` 항목) | path | {sum(paths.values())} | {cells} |")
    return "\n".join(
        [
            GENERATED_NOTE,
            "",
            "| 파일 | 생태계 | 항목 수 | allow | 승인된 예외 | review 면제(development) | review | deny |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def render_violations(findings: list[Finding]) -> str:
    groups: dict[tuple[str, str, str, str, str], tuple[set[str], set[str]]] = {}
    for f in findings:
        if f.outcome in FAILING:
            versions, lockfiles = groups.setdefault((f.outcome, f.ecosystem, f.name, f.license, f.rule), (set(), set()))
            if f.version:
                versions.add(f.version)
            lockfiles.add(f.lockfile)
    rows = []
    for (outcome, eco, name, lic, rule), (versions, lockfiles) in sorted(
        groups.items(), key=lambda kv: (kv[0][0] != "deny", kv[0][1], kv[0][2], kv[0][3])
    ):
        where = ", ".join(x if eco == "path" else f"`{short_path(x)}`" for x in sorted(lockfiles))
        cells = [outcome, eco, f"`{name}`", ", ".join(sorted(versions)), f"`{lic}`" if lic else "", where, rule]
        rows.append("| " + " | ".join(md_cell(c) for c in cells) + " |")
    failing = [f for f in findings if f.outcome in FAILING]
    return "\n".join(
        [
            GENERATED_NOTE,
            "",
            f"`--check`가 실패로 세는 항목: 잠금 파일별 {len(failing)}건, 아래 표 {len(rows)}줄.",
            "",
            "| 판정 | 생태계 | 이름 | 버전 | 찾은 라이선스 | 잠금 파일 | 규칙 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def top_label(eco: str, lic: str, count: int) -> str:
    if eco == "pip":
        kind, _, val = lic.partition(":")
        return f"{PIP_LABEL[kind]} `{val}` {count}"
    return f"`{lic}` {count}"


def render_top(files: list[Lockfile], data: dict[str, list[Entry]]) -> str:
    go_paths = [f.path for f in files if f.counted and f.ecosystem == "go"]
    go_lines = sum(len(data[p]) for p in go_paths)
    names = {
        "pip": f"pip(`{TOP_PATHS['pip']}`)",
        "npm": f"npm(`{TOP_PATHS['npm']}`)",
        "cargo": f"cargo(`{TOP_PATHS['cargo']}`)",
        "go": f"go({len(go_paths)}개 `go.mod` 합계 {go_lines}줄)",
    }
    rows = []
    for eco in ECOSYSTEMS:
        entries = [e for p in go_paths for e in data[p]] if eco == "go" else data.get(TOP_PATHS[eco], [])
        counts = Counter(e.license for e in entries)
        # Equal counts sort by license name, descending, so a rerun never reorders the table.
        top = sorted(counts.items(), key=lambda kv: kv[0], reverse=True)
        top = sorted(top, key=lambda kv: -kv[1])[:5]
        rows.append(f"| {names[eco]} | {', '.join(top_label(eco, k, v) for k, v in top)} | {TOP_BASIS[eco]} |")
    return "\n".join([GENERATED_NOTE, "", "| 생태계 | 상위 5개 | 기준 |", "| --- | --- | --- |", *rows])


def render_allow(policy: Policy) -> str:
    listed = ", ".join(f"`{x}`" for x in policy.allow)
    return "\n".join([GENERATED_NOTE, "", f"허용 목록(`{POLICY_FILE}`의 `[allow]`): {listed}."])


def replace_region(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- generated:{name}:begin -->).*?(<!-- generated:{name}:end -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"licenses.md has no `generated:{name}` region")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text, count=1)


def tsv_line(f: Finding) -> str:
    return "\t".join((f.outcome, f.lockfile, f.name, f.version or "-", f.license or "-", f.rule))


def report(policy: Policy, findings: list[Finding]) -> bool:
    """Print every failing finding to stdout and a count to stderr. Return True when the check fails."""
    failing = [f for f in findings if f.outcome in FAILING]
    for f in sorted(failing, key=lambda f: (f.outcome != "deny", f.lockfile, f.name, f.version)):
        print(tsv_line(f))  # noqa: T201
    counts = Counter(f.outcome for f in failing)
    unique = len({(f.ecosystem, f.name, f.version) for f in failing})
    print(  # noqa: T201
        f"{POLICY_FILE}: {len(failing)} violations ({counts['deny']} deny, {counts['review']} review)"
        f" over {unique} distinct packages and paths",
        file=sys.stderr,
    )
    if failing and policy.status != "adopted":
        print(f"{POLICY_FILE}: status is {policy.status}, so violations do not fail the check", file=sys.stderr)  # noqa: T201
        return False
    return bool(failing)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="exit 1 on a deny or unapproved review verdict, or when licenses.md differs from the output",
    )
    mode.add_argument(
        "--list",
        action="store_true",
        help="print outcome, lockfile, name, version, license and rule of every entry that is not allow, and write no page",
    )
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="repository root")
    ap.add_argument("--cache-dir", type=Path, help="directory outside the repository for registry answers")
    args = ap.parse_args()

    root: Path = args.root.resolve()
    if args.cache_dir:
        cache_dir = args.cache_dir.resolve()
        if cache_dir == root or root in cache_dir.parents:
            sys.exit("--cache-dir must be outside the repository")
    else:
        cache_dir = None
    if shutil.which("cargo") is None:
        sys.exit("cargo is required for the Rust lockfiles")

    today = datetime.date.today().isoformat()
    policy = load_policy(root, today)
    if policy.review_by and policy.review_by < today:
        print(f"warning: {POLICY_FILE} review_by {policy.review_by} has passed", file=sys.stderr)  # noqa: T201
    page = root / "wiki" / "licenses.md"
    notes = load_notes(root / "wiki" / "_tools" / "licenses-notes.tsv")
    tracked = git_files(root)
    paths = sorted(p for p in tracked if LOCKFILE.search(p))
    files = [describe(root, p) for p in paths]
    unknown = sorted(p for p in set(paths) - set(notes) if not p.endswith("go.sum"))
    stale = sorted(set(notes) - set(paths))
    if unknown:
        print(f"warning: no notes row for: {', '.join(unknown)} (note shown as 미확인)", file=sys.stderr)  # noqa: T201
    if stale:
        print(f"warning: notes rows without a lockfile: {', '.join(stale)}", file=sys.stderr)  # noqa: T201

    data = collect(root, files, Cache(cache_dir, fetch_tag()))
    eco_of = {f.path: f.ecosystem for f in files}
    failed = {(eco_of[p], e.name, e.version) for p, es in data.items() for e in es if is_error(e.license)}
    if failed:
        print(f"error: {len(failed)} registry lookups failed; nothing written. First ones:", file=sys.stderr)  # noqa: T201
        for eco, name, version in sorted(failed)[:10]:
            print(f"  {eco} {name} {version}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    findings = judge_all(policy, files, data, tracked)

    if args.list:
        for f in findings:
            if f.outcome != "allow":
                print(tsv_line(f))  # noqa: T201
        return

    old = page.read_text()
    new = replace_region(old, "scope", render_scope(files, notes))
    new = replace_region(new, "summary", render_summary(files, notes, findings))
    new = replace_region(new, "violations", render_violations(findings))
    new = replace_region(new, "top", render_top(files, data))
    new = replace_region(new, "allow", render_allow(policy))

    if args.check:
        failed_check = report(policy, findings)
        if new != old:
            print("wiki/licenses.md is out of date; run wiki/_tools/gen_licenses.py", file=sys.stderr)  # noqa: T201
            failed_check = True
        if failed_check:
            sys.exit(1)
        return
    if new != old:
        page.write_text(new)
        print(f"updated {page.relative_to(root)}")  # noqa: T201
    else:
        print("already up to date")  # noqa: T201


if __name__ == "__main__":
    main()
