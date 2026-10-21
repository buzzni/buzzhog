from infi.clickhouse_orm import migrations


def create_materialized_columns(database):
    # Materializing columns is not available in this build.
    return


operations = [migrations.RunPython(create_materialized_columns)]
