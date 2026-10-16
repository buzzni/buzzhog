#!/usr/bin/env python3
"""Regenerate the generated regions of wiki/modules.md.

Usage, from the repository root:

    python3 -I wiki/_tools/gen_modules.py            # rewrite wiki/modules.md in place
    python3 -I wiki/_tools/gen_modules.py --check    # exit 1 when modules.md is out of date

The script reads `products/`, `posthog/`, `frontend/src/` and `tach.toml`.
It writes nothing except `wiki/modules.md`.
Hand-written columns (role, verdict) come from `wiki/_tools/modules-notes.tsv`.
"""

from __future__ import annotations

import os
import re
import sys
import tomllib
import argparse
import subprocess
from collections import defaultdict
from pathlib import Path

CODE_EXT = {".py", ".ts", ".tsx", ".rs", ".go", ".js", ".jsx"}
SKIP_DIRS = {"node_modules", "__pycache__", "generated", "migrations", "__snapshots__"}
TEST_DIRS = {"tests", "test", "__tests__", "evals"}
OUTSIDE_TOPS = ["posthog", "frontend/src"]
EE_TEST_PATH = re.compile(r"/tests?/|/test_[^/]*$|_test\.py$|conftest")

PY_IMPORT = re.compile(r"^\s*(?:from|import)\s+(products\.(\w+)|posthog\b|ee\b)", re.M)
TS_IMPORT = re.compile(r"""from\s+['"](?:products/(\w+)|@posthog/products-([\w-]+)|scenes/|lib/|~/)""")
OUTSIDE_IMPORT = re.compile(
    r"(?:^\s*(?:from|import)\s+products\.(\w+)|['\"]products/(\w+)/|@posthog/products-([\w-]+))", re.M
)

NOTES_HEADER = "module\trole\tflags\tevidence\tverdict\treason"
VERDICTS = ("핵심", "유지", "검토", "제거 후보")
FLAGS = {"internal", "stub", "cloud", "external"}
TABLE_HEADER = (
    "| 모듈 | 역할 (플래그) — 근거 | BE | FE | 파일 | LOC | 나가는 의존 (상위 4) "
    "| 들어옴: product · 코어 · 프론트 | `ee` import | 판단 · 근거 |\n"
    "|---|---|---|---|---:|---:|---|---|---:|---|"
)
GENERATED_NOTE = (
    "Generated from `wiki/_tools/gen_modules.py` and `wiki/_tools/modules-notes.tsv` — Do not edit by hand."
)


def is_test(parts: set[str], fname: str) -> bool:
    return bool(TEST_DIRS & parts) or fname.startswith("test_") or ".test." in fname or ".stories." in fname


def walk_code(base: Path):
    """Yield (path, relative parts) for code files, pruning skipped directories."""
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            path = Path(dirpath, fname)
            if path.suffix in CODE_EXT:
                yield path, path.relative_to(base).parts


def scan_products(root: Path) -> dict[str, dict]:
    products_dir = root / "products"
    names = sorted(d.name for d in products_dir.iterdir() if d.is_dir() and not d.name.startswith(("_", ".")))
    out: dict[str, dict] = {}
    for name in names:
        d = products_dir / name
        files = loc = 0
        dep_py: dict[str, int] = defaultdict(int)
        dep_ts: dict[str, int] = defaultdict(int)
        for f, rel in walk_code(d):
            text = f.read_text(errors="ignore")
            files += 1
            loc += text.count("\n")
            if is_test(set(rel), f.name):
                continue
            if f.suffix == ".py":
                for m in PY_IMPORT.finditer(text):
                    if m.group(2) and m.group(2) != name:
                        dep_py[m.group(2)] += 1
            elif f.suffix in (".ts", ".tsx"):
                for m in TS_IMPORT.finditer(text):
                    other = m.group(1) or (m.group(2) or "").replace("-", "_")
                    if other and other != name:
                        dep_ts[other] += 1
        out[name] = {
            "backend": (d / "backend").is_dir(),
            "frontend": (d / "frontend").is_dir(),
            "files": files,
            "loc": loc,
            "dep_py": dict(dep_py),
            "dep_ts": dict(dep_ts),
            "inbound_products": set(),
            "inbound_core": 0,
            "inbound_frontend": 0,
        }
    for name, v in out.items():
        for other in list(v["dep_py"]) + list(v["dep_ts"]):
            if other in out:
                out[other]["inbound_products"].add(name)
    for top in OUTSIDE_TOPS:
        base = root / top
        if not base.exists():
            continue
        for f, rel in walk_code(base):
            if f.suffix not in (".py", ".ts", ".tsx") or is_test(set(rel), f.name):
                continue
            for m in OUTSIDE_IMPORT.finditer(f.read_text(errors="ignore")):
                other = m.group(1) or m.group(2) or (m.group(3) or "").replace("-", "_")
                if other not in out:
                    continue
                if top == "posthog":
                    out[other]["inbound_core"] += 1
                elif top == "frontend/src":
                    out[other]["inbound_frontend"] += 1
    return out


def count_ee_imports(root: Path) -> dict[str, int]:
    """Count non-test Python files per product that import the removed `ee/` package."""
    counts: dict[str, int] = defaultdict(int)
    out = subprocess.run(
        ["grep", "-rlE", r"^\s*(from|import) ee(\.| )", "--include=*.py", "products"],
        cwd=root,
        capture_output=True,
        text=True,
    ).stdout
    for path in out.split():
        if not EE_TEST_PATH.search(path):
            counts[path.split("/")[1]] += 1
    return dict(counts)


def tach_ee_stats(root: Path) -> tuple[int, int, int]:
    """Return (lines with "ee", modules with "ee" in depends_on, of those not under products)."""
    text = (root / "tach.toml").read_text()
    lines = sum(1 for line in text.splitlines() if '"ee"' in line)
    modules = tomllib.loads(text)["modules"]
    with_ee = [
        m["path"]
        for m in modules
        if "ee" in [d if isinstance(d, str) else d.get("path") for d in m.get("depends_on", [])]
    ]
    return lines, len(with_ee), sum(1 for p in with_ee if not p.startswith("products."))


def mutual_pairs(scan: dict[str, dict]) -> list[tuple[str, str]]:
    edges = {(n, o) for n, v in scan.items() for o in list(v["dep_py"]) + list(v["dep_ts"]) if o in scan}
    return sorted({tuple(sorted(e)) for e in edges if (e[1], e[0]) in edges})


def load_notes(path: Path) -> dict[str, dict[str, str]]:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != NOTES_HEADER:
        sys.exit(f"{path}: first line must be {NOTES_HEADER!r}")
    notes: dict[str, dict[str, str]] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) != 6:
            sys.exit(f"{path}: expected 6 tab-separated columns: {line!r}")
        name, row = cols[0], dict(zip(NOTES_HEADER.split("\t")[1:], cols[1:]))
        if name in notes:
            sys.exit(f"{path}: duplicate row for {name!r}")
        # A misspelled verdict would silently drop the module from the core table and the distribution.
        if row["verdict"] not in VERDICTS:
            sys.exit(f"{path}: {name}: verdict {row['verdict']!r} is not one of {', '.join(VERDICTS)}")
        bad_flags = set(row["flags"].split(",")) - FLAGS - {"", "none"}
        if bad_flags:
            sys.exit(f"{path}: {name}: unknown flags {sorted(bad_flags)}; use {', '.join(sorted(FLAGS))}")
        notes[name] = row
    return notes


def fmt_deps(v: dict, scan: dict) -> str:
    merged: dict[str, int] = defaultdict(int)
    for k, c in list(v["dep_py"].items()) + list(v["dep_ts"].items()):
        if k in scan:
            merged[k] += c
    items = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
    text = ", ".join(f"`{k}`" for k, _ in items[:4])
    if len(items) > 4:
        text += f" 외 {len(items) - 4}"
    return text or "—"


def flag(x: bool) -> str:
    return "O" if x else "—"


def table_rows(scan: dict, notes: dict, ee: dict[str, int]) -> list[str]:
    rows = []
    for name in sorted(scan):
        v = scan[name]
        n = notes.get(name, {"role": "미확인", "flags": "", "evidence": "", "verdict": "미확인", "reason": ""})
        flags = "" if n["flags"] in ("", "none") else f" ({n['flags']})"
        evidence = f" — `{n['evidence']}`" if n["evidence"] else ""
        rows.append(
            f"| `{name}` | {n['role']}{flags}{evidence} | {flag(v['backend'])} | {flag(v['frontend'])} "
            f"| {v['files']:,} | {v['loc']:,} | {fmt_deps(v, scan)} "
            f"| {len(v['inbound_products'])} · {v['inbound_core']} · {v['inbound_frontend']} "
            f"| {ee.get(name, 0) or '—'} | **{n['verdict']}** {n['reason']} |"
        )
    return rows


def render_stats(scan: dict, notes: dict, ee: dict[str, int], root: Path) -> str:
    verdicts = [notes[n]["verdict"] for n in scan if n in notes]
    dist = ", ".join(f"{k} {verdicts.count(k)}" for k in VERDICTS)
    tach_lines, tach_modules, tach_other = tach_ee_stats(root)
    top_ee = sorted(ee.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    return "\n".join(
        [
            GENERATED_NOTE,
            "",
            f"- `products/` 아래 디렉터리는 {len(scan)}개다.",
            f"- `backend/` 디렉터리가 있는 모듈은 {sum(v['backend'] for v in scan.values())}개, "
            f"`frontend/` 디렉터리가 있는 모듈은 {sum(v['frontend'] for v in scan.values())}개다.",
            f"- 판단 분포: {dist}.",
            f"- 서로 import하는(양방향) product 쌍은 {len(mutual_pairs(scan))}개다.",
            f"- 지워진 `ee/`를 import하는 비테스트 파일이 있는 product는 {len(ee)}개다.",
            "  많은 순서: " + ", ".join(f"`{k}` {c}" for k, c in top_ee) + ".",
            f'- `tach.toml`에는 `"ee"`가 {tach_lines}번 나온다.',
            f'  `depends_on`에 `"ee"`를 둔 모듈은 {tach_modules}개이고, 그중 product가 아닌 모듈은 {tach_other}개다.',
        ]
    )


def render_core(scan: dict, notes: dict) -> str:
    core = [n for n in scan if n in notes and notes[n]["verdict"] == "핵심"]
    core.sort(key=lambda n: (-(len(scan[n]["inbound_products"]) + scan[n]["inbound_core"]), n))
    lines = [
        GENERATED_NOTE,
        "",
        "| 모듈 | 들어오는 import (product 수 · 코어 · 프론트) |",
        "|---|---|",
    ]
    for n in core:
        v = scan[n]
        suffix = " (프론트 전용)" if not v["backend"] else ""
        lines.append(
            f"| `{n}` | {len(v['inbound_products'])} · {v['inbound_core']} · {v['inbound_frontend']}{suffix} |"
        )
    return "\n".join(lines)


def render_table(scan: dict, notes: dict, ee: dict[str, int]) -> str:
    return "\n".join([GENERATED_NOTE, "", TABLE_HEADER, *table_rows(scan, notes, ee)])


def replace_region(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- generated:{name}:begin -->).*?(<!-- generated:{name}:end -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"modules.md has no `generated:{name}` region")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text, count=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 when modules.md differs from the output")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="repository root")
    args = ap.parse_args()

    root: Path = args.root
    page = root / "wiki" / "modules.md"
    notes = load_notes(root / "wiki" / "_tools" / "modules-notes.tsv")
    scan = scan_products(root)
    ee = count_ee_imports(root)

    unknown = sorted(set(scan) - set(notes))
    stale = sorted(set(notes) - set(scan))
    if unknown:
        print(f"warning: no notes row for: {', '.join(unknown)} (shown as 미확인)", file=sys.stderr)  # noqa: T201
    if stale:
        print(f"warning: notes rows without a product directory: {', '.join(stale)}", file=sys.stderr)  # noqa: T201

    old = page.read_text()
    new = replace_region(old, "stats", render_stats(scan, notes, ee, root))
    new = replace_region(new, "core", render_core(scan, notes))
    new = replace_region(new, "table", render_table(scan, notes, ee))

    if args.check:
        if new != old:
            print("wiki/modules.md is out of date; run wiki/_tools/gen_modules.py", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        return
    if new != old:
        page.write_text(new)
        print(f"updated {page.relative_to(root)}")  # noqa: T201
    else:
        print("already up to date")  # noqa: T201


if __name__ == "__main__":
    main()
