import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0003_teamaccesscontrolconfig"),
        ("feature_flags", "0001_squash_2026_09_07_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeatureFlagRoleAccess",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "feature_flag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access",
                        related_query_name="access",
                        to="feature_flags.featureflag",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feature_flag_access",
                        related_query_name="feature_flag_access",
                        to="access_control.role",
                    ),
                ),
            ],
            options={
                "db_table": "ee_featureflagroleaccess",
                "constraints": [
                    models.UniqueConstraint(fields=("role", "feature_flag"), name="unique_feature_flag_and_role")
                ],
            },
        ),
    ]
