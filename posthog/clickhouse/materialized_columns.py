from collections.abc import Mapping

from posthog.clickhouse.materialized_column_types import (
    DMAT_STRING_COLUMN_NAME_PREFIX,
    MATERIALIZATION_VALID_TABLES,
    MATERIALIZED_COLUMN_NAME_PREFIXES,
    ColumnName,
    MaterializedColumn,
    TablesWithMaterializedColumns,
)
from posthog.models.property import PropertyName, TableColumn
from posthog.property_columns import TableWithProperties

__all__ = [
    "DMAT_STRING_COLUMN_NAME_PREFIX",
    "MATERIALIZATION_VALID_TABLES",
    "MATERIALIZED_COLUMN_NAME_PREFIXES",
    "ColumnName",
    "MaterializedColumn",
    "TableWithProperties",
    "TablesWithMaterializedColumns",
    "get_enabled_materialized_columns_by_table",
    "get_materialized_column_for_property",
]


def get_materialized_column_for_property(
    table: TablesWithMaterializedColumns, table_column: TableColumn, property_name: PropertyName
) -> MaterializedColumn | None:
    return None


def get_enabled_materialized_columns_by_table() -> Mapping[
    TablesWithMaterializedColumns, Mapping[tuple[PropertyName, TableColumn], MaterializedColumn]
]:
    return {}
