#!/usr/bin/env python3
"""Tests for the policy classifier of gen_licenses.py. Run: python3 -I wiki/_tools/test_gen_licenses.py"""

from __future__ import annotations

import sys
import tomllib
import importlib.util
from pathlib import Path

import unittest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gen_licenses", HERE / "gen_licenses.py")
assert _spec and _spec.loader
gen = importlib.util.module_from_spec(_spec)
sys.modules["gen_licenses"] = gen
_spec.loader.exec_module(gen)

TODAY = "2026-10-21"
POLICY = """
schema = 1
status = "adopted"

[allow]
licenses = ["MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0"]

[deny]
licenses = ["AGPL-3.0-only", "LicenseRef-Commons-Clause"]
prefixes = ["AGPL-", "PolyForm-", "LicenseRef-PolyForm-"]

[review]
licenses = ["GPL-2.0-only", "LGPL-3.0-or-later"]
prefixes = ["GPL-", "LGPL-", "MPL-", "LicenseRef-"]

[scope]
distributed = { deny = "fail", review = "fail" }
development = { deny = "fail", review = "exempt" }

[approval]
require_one_of = ["version", "review_by"]

[expression]
or = "best"
and = "worst"
with = "base-unless-deny"
slash = "or"
plus = "strip"

[expression.alias]
"BSD" = "BSD-3-Clause"

[[package]]
ecosystem = "npm"
name = "proposed-mit"
license = "MIT"
verdict = "allow"
reason = "r"
status = "proposed"
scope = "development"

[[package]]
ecosystem = "npm"
name = "proposed-agpl"
reason = "r"
status = "proposed"

[[package]]
ecosystem = "npm"
name = "rejected-*"
reason = "r"
status = "rejected"

[[package]]
ecosystem = "npm"
name = "pinned"
version = "1.0.0"
verdict = "allow"
reason = "r"
status = "approved"

[[package]]
ecosystem = "npm"
name = "unpinned"
verdict = "allow"
reason = "r"
status = "approved"

[[package]]
ecosystem = "npm"
name = "expired"
verdict = "allow"
reason = "r"
status = "approved"
review_by = "2026-01-01"

[[package]]
ecosystem = "npm"
name = "approved-license"
license = "GPL-2.0-only"
reason = "r"
status = "approved"
review_by = "2027-01-01"
scope = "development"

[[package]]
ecosystem = "npm"
name = "approved-deny"
reason = "r"
status = "approved"
review_by = "2027-01-01"
"""


def policy() -> gen.Policy:
    return gen.Policy(tomllib.loads(POLICY), TODAY)


class TestEvaluate(unittest.TestCase):
    CASES = [
        ("MIT", "allow"),
        ("mit", "allow"),
        ("BSD", "allow"),
        ("MPL-2.0", "allow"),
        ("MPL-1.1", "review"),
        ("MIT OR GPL-2.0-only", "allow"),
        ("MIT AND GPL-2.0-only", "review"),
        ("(MIT OR Apache-2.0) AND AGPL-3.0-only", "deny"),
        ("MIT/Apache-2.0", "allow"),
        ("GPL-2.0+", "review"),
        ("AGPL-1.0", "deny"),
        ("Apache-2.0 WITH LLVM-exception", "allow"),
        ("Apache-2.0 WITH Commons-Clause", "deny"),
        ("MIT AND Commons-Clause", "deny"),
        ("PolyForm-Strict-1.0.0", "deny"),
        ("LicenseRef-PolyForm-Strict-1.0.0", "deny"),
        ("UNKNOWN", "review"),
        ("SEE LICENSE IN LICENSE", "review"),
        ("UNKNOWN(LICENSE)", "review"),
        ("(MIT", "review"),
        ("MIT AND", "review"),
        ("", "review"),
    ]

    def test_expressions(self) -> None:
        p = policy()
        for expr, verdict in self.CASES:
            with self.subTest(expr=expr):
                self.assertEqual(p.evaluate(expr).verdict, verdict)


class TestFoundExpression(unittest.TestCase):
    CASES = [
        ("pip", "E:MIT AND Apache-2.0", "MIT AND Apache-2.0"),
        ("pip", "C:OSI Approved;MIT License", "MIT"),
        ("pip", "C:Apache Software License;BSD License", "Apache-2.0 AND BSD"),
        ("pip", "C:Other/Proprietary License", None),
        ("pip", "C:OSI Approved", None),
        ("pip", "R:Apache License 2.0", "Apache-2.0"),
        ("pip", "R:MIT style", "MIT style"),
        ("pip", "R:", None),
        ("pip", "R:ERR timeout", None),
        ("cargo", "FILE:LICENSE", None),
        ("npm", "MIT", "MIT"),
    ]

    def test_found_expression(self) -> None:
        for eco, lic, expr in self.CASES:
            with self.subTest(lic=lic):
                self.assertEqual(gen.found_expression(eco, lic), expr)


class TestJudge(unittest.TestCase):
    CASES = [
        # name, version, found license, lockfile scope, outcome
        ("plain", "1.0.0", "MIT", "distributed", "allow"),
        ("plain", "1.0.0", "GPL-2.0-only", "distributed", "review"),
        ("plain", "1.0.0", "GPL-2.0-only", "development", "exempt"),
        ("plain", "1.0.0", "AGPL-3.0-only", "development", "deny"),
        ("proposed-mit", "1.0.0", "SEE LICENSE IN LICENSE", "distributed", "review"),
        ("proposed-agpl", "1.0.0", "AGPL-3.0-only", "development", "deny"),
        ("rejected-thing", "2.0.0", "MIT", "distributed", "deny"),
        ("pinned", "1.0.0", "UNKNOWN", "distributed", "exception"),
        ("pinned", "2.0.0", "UNKNOWN", "distributed", "review"),
        ("unpinned", "1.0.0", "UNKNOWN", "distributed", "review"),
        ("expired", "1.0.0", "UNKNOWN", "distributed", "review"),
        ("approved-license", "1.0.0", "UNKNOWN", "distributed", "exception"),
        ("approved-deny", "1.0.0", "AGPL-3.0-only", "distributed", "deny"),
    ]

    def test_outcomes(self) -> None:
        p = policy()
        for name, version, lic, scope, outcome in self.CASES:
            with self.subTest(name=name, version=version, scope=scope):
                found = p.evaluate(gen.found_expression("npm", lic))
                judged = p.judge(found, p.decision_for("npm", name, version), scope)
                self.assertEqual(judged.outcome, outcome, judged.rule)

    def test_rejects_a_policy_with_another_with_rule(self) -> None:
        data = tomllib.loads(POLICY)
        data["expression"]["with"] = "base"
        with self.assertRaises(SystemExit):
            gen.Policy(data, TODAY)

    def test_repository_policy_loads(self) -> None:
        gen.load_policy(HERE.parents[1], TODAY)


class TestGlob(unittest.TestCase):
    CASES = [
        ("a/{x,y}.bin", "a/y.bin", True),
        ("a/{x,y}.bin", "a/z.bin", False),
        ("a/*.png", "a/b/c.png", False),
        ("a/**/F/*", "a/F/f.ttf", True),
        ("a/**/F/*", "a/b/c/F/f.ttf", True),
        ("a/b/**", "a/b/c/d.ts", True),
        ("a/b/**", "a/bc/d.ts", False),
    ]

    def test_globs(self) -> None:
        for glob, path, hit in self.CASES:
            with self.subTest(glob=glob, path=path):
                self.assertEqual(bool(gen.glob_regex(glob).match(path)), hit)


if __name__ == "__main__":
    unittest.main()
