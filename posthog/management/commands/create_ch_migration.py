import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.timezone import now

MIGRATION_PATH = Path("posthog/clickhouse/migrations")
MAX_MIGRATION_FILE = MIGRATION_PATH / "max_migration.txt"

FILE_DEFAULT = """operations = []
"""

_MIGRATION_FILE_PATTERN = re.compile(r"^(\d{4})_.+\.py$")


# ex: python manage.py create_ch_migration <name of migration>
class Command(BaseCommand):
    help = "Create blank clickhouse migration"

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str)

    def handle(self, *args, **options):
        name = options["name"]

        # default to auto syntax
        if not name:
            name = now().strftime("auto_%Y%m%d_%H%M")

        index_label = _format_number(_next_index(MIGRATION_PATH))
        migration_name = f"{index_label}_{name}"
        (MIGRATION_PATH / f"{migration_name}.py").write_text(FILE_DEFAULT, encoding="utf_8")
        MAX_MIGRATION_FILE.write_text(f"{migration_name}\n", encoding="utf_8")


def _next_index(migration_path: Path) -> int:
    # Migration numbers have gaps, so counting the directory entries would reuse a number.
    indexes = [
        int(match.group(1)) for path in migration_path.iterdir() if (match := _MIGRATION_FILE_PATTERN.match(path.name))
    ]
    return max(indexes, default=-1) + 1


def _format_number(num: int) -> str:
    return f"{num:04d}"
