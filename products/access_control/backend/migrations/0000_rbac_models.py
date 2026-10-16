import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import posthog.uuidt


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("posthog", "0001_squash_2026_09_07_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.UUIDField(default=posthog.uuidt.UUIDT, editable=False, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "feature_flags_access_level",
                    models.PositiveSmallIntegerField(
                        choices=[(21, "Can only view"), (37, "Can always edit")], default=37
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="roles",
                        related_query_name="role",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        related_query_name="role",
                        to="posthog.organization",
                    ),
                ),
            ],
            options={
                "db_table": "ee_role",
            },
        ),
        migrations.CreateModel(
            name="RoleMembership",
            fields=[
                (
                    "id",
                    models.UUIDField(default=posthog.uuidt.UUIDT, editable=False, primary_key=True, serialize=False),
                ),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "organization_member",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_memberships",
                        related_query_name="role_membership",
                        to="posthog.organizationmembership",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        related_query_name="role",
                        to="access_control.role",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_memberships",
                        related_query_name="role_membership",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "ee_rolemembership",
            },
        ),
        migrations.AddField(
            model_name="role",
            name="members",
            field=models.ManyToManyField(through="access_control.RoleMembership", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="OrganizationResourceAccess",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "resource",
                    models.CharField(
                        choices=[
                            ("feature flags", "feature flags"),
                            ("experiments", "experiments"),
                            ("cohorts", "cohorts"),
                            ("data management", "data management"),
                            ("session recordings", "session recordings"),
                            ("insights", "insights"),
                            ("dashboards", "dashboards"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "access_level",
                    models.PositiveSmallIntegerField(
                        choices=[(21, "Can only view"), (37, "Can always edit")], default=37
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resource_access",
                        to="posthog.organization",
                    ),
                ),
            ],
            options={
                "db_table": "ee_organizationresourceaccess",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("organization", "resource"), name="unique resource per organization"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="AccessControl",
            fields=[
                (
                    "id",
                    models.UUIDField(default=posthog.uuidt.UUIDT, editable=False, primary_key=True, serialize=False),
                ),
                ("access_level", models.CharField(max_length=32)),
                ("resource", models.CharField(max_length=32)),
                ("resource_id", models.CharField(max_length=36, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "organization_member",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to="posthog.organizationmembership",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to="posthog.team",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_controls",
                        related_query_name="access_controls",
                        to="access_control.role",
                    ),
                ),
            ],
            options={
                "db_table": "ee_accesscontrol",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("resource", "resource_id", "team", "organization_member", "role"),
                        name="unique resource per target",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="rolemembership",
            constraint=models.UniqueConstraint(fields=("role", "user"), name="unique_user_and_role"),
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(fields=("organization", "name"), name="unique_role_name"),
        ),
    ]
