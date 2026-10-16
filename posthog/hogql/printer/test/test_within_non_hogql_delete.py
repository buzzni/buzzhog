"""Tests the ``within_non_hogql_query`` lightweight-DELETE-mutation path.

Data deletion compiles a HogQL property predicate into a ClickHouse fragment via ``compile_hogql_predicate`` (which sets
``within_non_hogql_query=True``), and the deletion DAG splices that fragment into a lightweight
``DELETE FROM sharded_events WHERE …`` mutation. The catch: a ClickHouse lightweight-delete expression analyzer rejects
table-qualified column references, so when the predicate hits a materialized column the fragment must read it
**unqualified** — ``mat_$browser``, never ``sharded_events.mat_$browser`` — even though the column exists on every
replica. The DAG tests (``posthog/dags/tests/test_data_deletion_requests.py``) cover the delete flow only over an
unmaterialized property, so the materialized-column case is tested here.

This file checks two things:

1. ``compile_hogql_predicate`` over ``properties.$browser = 'Chrome'`` with ``$browser`` materialized produces an
   unqualified fragment (no ``events.`` / ``sharded_events.`` prefix on the mat column) using only mutation-safe scalar
   functions.
2. A real lightweight DELETE built from that fragment (mirroring the production ``LightweightDeleteMutationRunner``
   statement and settings) removes the matching rows and leaves the non-matching and other-team rows in place.
"""

import re

from posthog.test.base import (
    APIBaseTest,
    ClickhouseTestMixin,
)


from posthog.clickhouse.client.execute import sync_execute
from posthog.models import Team
from posthog.models.data_deletion_request import compile_hogql_predicate
from posthog.models.event.sql import EVENTS_DATA_TABLE
from posthog.settings.data_stores import CLICKHOUSE_DATABASE


class _PredicateObj:
    """Minimal stand-in for the deletion-request shape ``compile_hogql_predicate`` reads (``team_id`` + predicate)."""

    def __init__(self, team_id: int, hogql_predicate: str) -> None:
        self.team_id = team_id
        self.hogql_predicate = hogql_predicate


# Functions a ClickHouse lightweight-delete mutation expression analyzer accepts: plain scalar functions. The compiled
# fragment for a property predicate must use only these (no aggregates, no table-qualified columns, no window/array
# higher-order forms). This is the allow-list the form constraint cares about.
_MUTATION_SAFE_FUNCTIONS = frozenset(
    {
        "equals",
        "notequals",
        "and",
        "or",
        "not",
        "ifnull",
        "isnull",
        "isnotnull",
        "nullif",
        "in",
        "notin",
        "has",
        "jsonextractraw",
        "jsonextractstring",
        "jsonhas",
        "replaceregexpall",
        "tostring",
        "like",
        "ilike",
        "lower",
        "greater",
        "less",
        "greaterorequals",
        "lessorequals",
    }
)


class TestWithinNonHogqlDelete(ClickhouseTestMixin, APIBaseTest):
    maxDiff = None

    def _assert_unqualified_and_mutation_safe(self, sql: str, expected_column_sql: str) -> None:
        sql_lower = sql.lower()
        expected_column_sql_lower = expected_column_sql.lower()

        # Unqualified — the lightweight-delete mutation analyzer rejects table-qualified column references.
        assert f"events.{expected_column_sql_lower}" not in sql_lower, (
            f"predicate column must be unqualified, got: {sql}"
        )
        assert "events." not in sql_lower, f"fragment must carry no table prefix at all, got: {sql}"
        assert "sharded_events." not in sql_lower, f"fragment must carry no table prefix at all, got: {sql}"
        # The unqualified physical property read must be present — confirms the mutation uses the active schema shape.
        assert expected_column_sql_lower in sql_lower, f"expected the property column {expected_column_sql} in: {sql}"

        # Mutation-safe: every function name used is on the scalar allow-list (no aggregates / unsafe forms).
        called = {name.lower() for name in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", sql)}
        unexpected = called - _MUTATION_SAFE_FUNCTIONS
        assert not unexpected, f"fragment uses non-mutation-safe functions {unexpected} in: {sql}"

    def _expected_browser_property_sql(self) -> str:
        return self._materialized_column_name("events", "$browser")

    def test_compiled_predicate_is_unqualified_and_mutation_safe_without_materialized_column(self) -> None:
        # Without materialization the fragment is the JSON-blob form; it must STILL be unqualified and mutation-safe
        # (the deletion path always runs with within_non_hogql_query=True). This is the other production shape.
        sql, _params = compile_hogql_predicate(_PredicateObj(self.team.pk, "properties.$browser = 'Chrome'"))

        sql_lower = sql.lower()
        assert "events." not in sql_lower, f"blob fragment must be unqualified, got: {sql}"
        assert "sharded_events." not in sql_lower, f"blob fragment must be unqualified, got: {sql}"
        assert "jsonextractraw" in sql_lower, f"expected the JSON-blob extract form, got: {sql}"
        called = {name.lower() for name in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", sql)}
        unexpected = called - _MUTATION_SAFE_FUNCTIONS
        assert not unexpected, f"blob fragment uses non-mutation-safe functions {unexpected} in: {sql}"

    def _count_browser_rows(self, team_id: int, browser: str) -> int:
        table = "events"
        browser_predicate = "JSONExtractString(properties, '$browser') = %(b)s"
        result = sync_execute(
            f"SELECT count() FROM {table} WHERE team_id = %(team_id)s AND {browser_predicate}",
            {"team_id": team_id, "b": browser},
        )
        return result[0][0]

    def _run_lightweight_delete(self, team_id: int, predicate_fragment: str, params: dict) -> None:
        # Mirror production ``LightweightDeleteMutationRunner.get_statement``: a lightweight ``DELETE FROM`` against the
        # local sharded table, scoped by team_id (the compiled fragment carries no team guard of its own) AND the
        # compiled predicate. Synchronous settings so the mutation completes before we assert.
        table = EVENTS_DATA_TABLE()
        delete_sql = (
            f"DELETE FROM {CLICKHOUSE_DATABASE}.{table} "  # nosemgrep: clickhouse-fstring-param-audit
            f"WHERE team_id = %(_del_team_id)s AND ({predicate_fragment})"
        )
        sync_execute(
            delete_sql,
            {**params, "_del_team_id": team_id},
            settings={"lightweight_deletes_sync": 2, "mutations_sync": 2},
        )

    def _run_and_assert_delete(self, predicate_fragment: str, params: dict, other_team: Team) -> None:
        # Pre-conditions.
        self.assertEqual(self._count_browser_rows(self.team.pk, "Chrome"), 5)
        self.assertEqual(self._count_browser_rows(self.team.pk, "Firefox"), 3)
        self.assertEqual(self._count_browser_rows(other_team.pk, "Chrome"), 1)

        self._run_lightweight_delete(self.team.pk, predicate_fragment, params)

        # Chrome rows for this team are gone; Firefox rows and the other team's Chrome row survive.
        self.assertEqual(self._count_browser_rows(self.team.pk, "Chrome"), 0)
        self.assertEqual(self._count_browser_rows(self.team.pk, "Firefox"), 3)
        self.assertEqual(self._count_browser_rows(other_team.pk, "Chrome"), 1)
