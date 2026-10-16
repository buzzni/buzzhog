#!/usr/bin/env python3
"""Regenerate the generated regions of wiki/licenses.md.

Usage, from the repository root:

    python3 -I wiki/_tools/gen_licenses.py                      # rewrite wiki/licenses.md in place
    python3 -I wiki/_tools/gen_licenses.py --check              # exit 1 when licenses.md is out of date
    python3 -I wiki/_tools/gen_licenses.py --cache-dir DIR      # keep registry answers in DIR between runs
    python3 -I wiki/_tools/gen_licenses.py --list               # print every entry outside 허용형 as TSV

The script reads the lockfiles that `git ls-files` lists, asks the package registries
(PyPI, the npm registry, the Go module proxy) for each license, and runs `cargo metadata --locked`.
It needs network access and `cargo`.
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
import hashlib
import inspect
import tomllib
import zipfile
import argparse
import tempfile
import subprocess
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

ALLOW = """MIT MIT-0 MIT-CMU X11 NCSA Apache-2.0 BSD BSD-2-Clause BSD-3-Clause 0BSD ISC Zlib BSL-1.0
Unlicense CC0-1.0 Python-2.0 PSF-2.0 CNRI-Python BlueOak-1.0.0 Unicode-3.0 Unicode-DFS-2016 OFL-1.1 AFL-2.1""".split()
ALLOW_LOWER = {x.lower() for x in ALLOW}
PIP_SYN = {
    "mit license": "MIT",
    "apache software license": "Apache-2.0",
    "bsd license": "BSD",
    "isc license (iscl)": "ISC",
    "python software foundation license": "PSF-2.0",
    "public domain": "CC0-1.0",
    "the unlicense (unlicense)": "Unlicense",
}
PIP_RAW = re.compile(r"^(mit|apache|bsd|3-clause bsd|isc|cc0|http://www\.opensource\.org/licenses/mit)", re.I)
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
CATEGORIES = ("permissive", "weak", "copyleft", "other")
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
    "Generated from `wiki/_tools/gen_licenses.py` and `wiki/_tools/licenses-notes.tsv` — Do not edit by hand."
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


def spdx_ok(expr: str) -> bool:
    toks = re.findall(r"\(|\)|[^\s()]+", expr.replace("/", " OR "))
    pos = 0

    def atom() -> bool:
        nonlocal pos
        if pos < len(toks) and toks[pos] == "(":
            pos += 1
            v = orx()
            pos += 1
            return v
        v = pos < len(toks) and toks[pos].lower() in ALLOW_LOWER
        pos += 1
        if pos < len(toks) and toks[pos].upper() == "WITH":
            pos += 2
        return v

    def andx() -> bool:
        nonlocal pos
        v = atom()
        while pos < len(toks) and toks[pos].upper() == "AND":
            pos += 1
            v = atom() and v
        return v

    def orx() -> bool:
        nonlocal pos
        v = andx()
        while pos < len(toks) and toks[pos].upper() == "OR":
            pos += 1
            v = andx() or v
        return v

    return bool(toks) and orx() and pos >= len(toks)


def classify(eco: str, lic: str) -> str:
    # spdx_ok takes one side of an `A OR B`, so a dual license with a permissive option counts as permissive.
    if spdx_ok(lic[2:] if eco == "pip" and lic.startswith("E:") else lic):
        return "permissive"
    if re.search(r"gpl|gnu", lic, re.I):
        return "copyleft"
    if re.search(r"\bmpl|mozilla|\bepl\b|eclipse public|cddl", lic, re.I):
        return "weak"
    if eco != "pip":
        return "permissive" if spdx_ok(lic) else "other"
    kind, _, val = lic.partition(":")
    if kind == "E":
        return "permissive" if spdx_ok(val) else "other"
    if kind == "C":
        parts = [p for p in val.split(";") if p not in ("OSI Approved", "DFSG approved")]
        return "permissive" if parts and all(PIP_SYN.get(p.lower()) for p in parts) else "other"
    return "permissive" if PIP_RAW.match(val) and "proprietary" not in val.lower() else "other"


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


def is_error(lic: str) -> bool:
    return lic.startswith(("ERR ", "R:ERR "))


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


def list_lockfiles(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.splitlines() if LOCKFILE.search(p))


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


def tally(entries: list[Entry], eco: str) -> Counter[str]:
    return Counter(classify(eco, e.license) for e in entries)


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


def render_summary(files: list[Lockfile], notes: dict[str, str], data: dict[str, list[Entry]]) -> str:
    order = [p for p in notes if p in data] + [f.path for f in files if f.counted and f.path not in notes]
    eco_of = {f.path: f.ecosystem for f in files}
    rows = []
    for p in order:
        c = tally(data[p], eco_of[p])
        rows.append(
            f"| `{short_path(p)}` | {eco_of[p]} | {len(data[p])} | {c['permissive']} | {c['weak']} | {c['copyleft']} | {c['other']} |"
        )
    return "\n".join(
        [
            GENERATED_NOTE,
            "",
            "| 파일 | 생태계 | 항목 수 | 허용형 | 약한 카피레프트(MPL, EPL, CDDL) | 강한·라이브러리 카피레프트(GPL, LGPL) | 비OSI·독점·미확인 |",
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


def render_allow() -> str:
    return "\n".join([GENERATED_NOTE, "", "허용 목록: " + ", ".join(f"`{x}`" for x in ALLOW) + "."])


def replace_region(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- generated:{name}:begin -->).*?(<!-- generated:{name}:end -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"licenses.md has no `generated:{name}` region")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 when licenses.md differs from the output")
    mode.add_argument(
        "--list",
        action="store_true",
        help="print category, lockfile, name, version and license of every entry outside 허용형, and write no page",
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

    page = root / "wiki" / "licenses.md"
    notes = load_notes(root / "wiki" / "_tools" / "licenses-notes.tsv")
    paths = list_lockfiles(root)
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

    if args.list:
        for path, entries in data.items():
            for e in entries:
                category = classify(eco_of[path], e.license)
                if category != "permissive":
                    print("\t".join((category, path, e.name, e.version, e.license)))  # noqa: T201
        return

    old = page.read_text()
    new = replace_region(old, "scope", render_scope(files, notes))
    new = replace_region(new, "summary", render_summary(files, notes, data))
    new = replace_region(new, "top", render_top(files, data))
    new = replace_region(new, "allow", render_allow())

    if args.check:
        if new != old:
            print("wiki/licenses.md is out of date; run wiki/_tools/gen_licenses.py", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        return
    if new != old:
        page.write_text(new)
        print(f"updated {page.relative_to(root)}")  # noqa: T201
    else:
        print("already up to date")  # noqa: T201


if __name__ == "__main__":
    main()
