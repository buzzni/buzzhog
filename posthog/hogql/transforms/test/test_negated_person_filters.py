import re
from dataclasses import dataclass

from posthog.test.base import APIBaseTest, QueryMatchingTest
from unittest.mock import patch

from parameterized import param, parameterized

from posthog.schema import HogQLQueryModifiers, MaterializationMode, PersonsOnEventsMode

from posthog.hogql import ast
from posthog.hogql.context import HogQLContext
from posthog.hogql.modifiers import create_default_modifiers_for_team
from posthog.hogql.parser import parse_select
from posthog.hogql.printer import prepare_and_print_ast
from posthog.hogql.property import property_to_expr

from posthog.models import PropertyDefinition

from products.event_definitions.backend.models.property_definition import PropertyType

JOINED = PersonsOnEventsMode.PERSON_ID_OVERRIDE_PROPERTIES_JOINED

INTERNAL = {"key": "email", "type": "person", "operator": "not_icontains", "value": "@internal.example"}
EXAMPLE = {"key": "email", "type": "person", "operator": "not_icontains", "value": "@example.com"}

INTERNAL_PERSONS = {"internal", "changed_to_internal", "merged"}
INTERNAL_OR_EXAMPLE_PERSONS = INTERNAL_PERSONS | {"external", "changed_to_external"}

PERSONS_JOIN = re.compile(r"AS \w+__person ON")


@dataclass(frozen=True)
class FakeMaterializedColumn:
    name: str
    type: str
    is_nullable: bool = False
    has_minmax_index: bool = False
    has_bloom_filter_index: bool = False
    has_ngram_lower_index: bool = False
    has_bloom_filter_lower_index: bool = False


MATERIALIZED_PERSON_COLUMNS = {
    "person": {
        (name, "properties"): FakeMaterializedColumn(name=f"pmat_{name}", type=column_type)
        for name, column_type in (("email", "String"), ("is_staff", "String"), ("score", "Float64"))
    }
}


class TestNegatedPersonFiltersPrinting(QueryMatchingTest, APIBaseTest):
    def setUp(self):
        super().setUp()
        self.enterContext(
            patch(
                "posthog.clickhouse.materialized_columns.get_enabled_materialized_columns_by_table",
                return_value=MATERIALIZED_PERSON_COLUMNS,
            )
        )
        PropertyDefinition.objects.create(
            team=self.team, name="is_staff", type=PropertyDefinition.Type.PERSON, property_type=PropertyType.Boolean
        )

    def _print(
        self,
        query: str,
        placeholders: dict[str, ast.Expr] | None = None,
        *,
        mode: PersonsOnEventsMode = JOINED,
        materialization_mode: MaterializationMode | None = None,
        team_on_context: bool = True,
    ) -> str:
        context = HogQLContext(
            team_id=self.team.pk,
            team=self.team if team_on_context else None,
            enable_select_queries=True,
            modifiers=create_default_modifiers_for_team(
                self.team,
                HogQLQueryModifiers(
                    personsOnEventsMode=mode,
                    materializationMode=materialization_mode,
                    negatedPersonFiltersNotIn=True,
                ),
            ),
        )
        sql, _ = prepare_and_print_ast(parse_select(query, placeholders=placeholders), context, dialect="clickhouse")
        return sql

    def test_rewrite_reads_only_persons_that_ever_matched(self):
        sql = self._print(
            "SELECT event FROM events WHERE {where}", {"where": property_to_expr([INTERNAL, EXAMPLE], self.team)}
        )

        assert not PERSONS_JOIN.search(sql)
        assert "where_optimization" in sql
        self.assertQueryMatchesSnapshot(sql)

    @parameterized.expand(
        [
            param("positive_filter_alongside", [INTERNAL, {"key": "email", "type": "person", "operator": "is_set"}]),
            param("person_field_selected", [INTERNAL], select="SELECT event, person.properties.name FROM events"),
            param("boolean_property", [{"key": "is_staff", "type": "person", "operator": "is_not", "value": "true"}]),
            param("join_drops_rows_without_a_person", [INTERNAL], inner_join=True),
            param("properties_on_events", [INTERNAL], mode=PersonsOnEventsMode.PERSON_ID_OVERRIDE_PROPERTIES_ON_EVENTS),
            param("not_events", [INTERNAL], select="SELECT distinct_id FROM person_distinct_ids"),
            param("property_not_materialized", [{**INTERNAL, "key": "$email"}]),
            param("persons_cte", [INTERNAL], select="WITH persons AS (SELECT 1 AS id) SELECT event FROM events"),
            param("materialization_disabled", [INTERNAL], materialization_mode=MaterializationMode.DISABLED),
            param(
                "typed_materialized_column", [{"key": "score", "type": "person", "operator": "is_not", "value": "0"}]
            ),
            param("team_id_only", [INTERNAL], team_on_context=False),
        ]
    )
    def test_keeps_the_join_when_the_rewrite_would_not_drop_it(
        self,
        _name: str,
        filters: list[dict],
        select: str = "SELECT event FROM events",
        mode: PersonsOnEventsMode = JOINED,
        inner_join: bool = False,
        materialization_mode: MaterializationMode | None = None,
        team_on_context: bool = True,
    ):
        with patch("posthog.hogql.database.schema.persons.posthoganalytics.feature_enabled", return_value=inner_join):
            sql = self._print(
                f"{select} WHERE {{where}}",
                {"where": property_to_expr(filters, self.team)},
                mode=mode,
                materialization_mode=materialization_mode,
                team_on_context=team_on_context,
            )

        assert "where_optimization" not in sql
        assert bool(PERSONS_JOIN.search(sql)) == (mode == JOINED)

    @parameterized.expand(
        [
            param(
                "self_join",
                "SELECT e.event FROM events e JOIN events f ON e.uuid = f.uuid"
                " WHERE e.person.properties.email != 'alice@internal.example'",
            ),
            param(
                "null_in_constant_list",
                "SELECT event FROM events WHERE person.properties.email NOT IN {excluded}",
                {"excluded": ast.Constant(value=[None, "alice@internal.example"])},
            ),
        ]
    )
    def test_keeps_the_join_for_hogql_the_rewrite_would_change(
        self, _name: str, query: str, placeholders: dict[str, ast.Expr] | None = None
    ):
        sql = self._print(query, placeholders)

        assert "where_optimization" not in sql
        assert PERSONS_JOIN.search(sql)
