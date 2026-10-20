from datetime import UTC, datetime, timedelta

from posthog.test.base import BaseTest
from unittest.mock import patch

from django.db import connection
from django.test import SimpleTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from parameterized import parameterized

from posthog.models.oauth import OAuthApplication
from posthog.models.organization import Organization
from posthog.models.project_secret_api_key import ProjectSecretAPIKey
from posthog.models.team.team import Team
from posthog.redis import get_client
from posthog.storage import team_llm_gateway_quota_cache as quota_cache
from posthog.storage.team_llm_gateway_quota_cache import (
    LLM_GATEWAY_QUOTA_CACHE_EXPIRY_SORTED_SET,
    LLM_GATEWAY_QUOTA_DEACTIVATED_TTL,
    LLM_GATEWAY_QUOTA_TTL_MARGIN_SECONDS,
    build_quota_blob,
    get_team_quota_blob,
    project_org_quota,
    project_team_quota,
    projected_team_ids,
    quota_blob_ttl,
    quota_blob_ttl_remaining,
    reconcile_quota_projection,
    team_llm_gateway_quota_hypercache as hypercache,
)

_GATEWAY_REDIS_URL = "redis://localhost:6379/15"
_NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=UTC)


class QuotaProjectionTestMixin(BaseTest):
    def setUp(self):
        super().setUp()
        hypercache.cache_client.clear()
        get_client(hypercache.redis_url).delete(LLM_GATEWAY_QUOTA_CACHE_EXPIRY_SORTED_SET)


class TestQuotaBlob(SimpleTestCase):
    def test_lapsed_score_is_not_a_limit(self):
        past = (_NOW - timedelta(seconds=1)).timestamp()
        self.assertIsNone(build_quota_blob(42, {"ai_credits": past}, True, _NOW))

    def test_unlimited_active_team_has_no_blob(self):
        self.assertIsNone(build_quota_blob(42, {}, True, _NOW))

    def test_limited_bucket_only_appears(self):
        until = (_NOW + timedelta(days=9)).timestamp()
        blob = build_quota_blob(42, {"posthog_code_credits": until}, True, _NOW)
        self.assertEqual(
            blob,
            {
                "team_id": 42,
                "version": 1,
                "buckets": {"posthog_code_credits": {"limited": True, "limited_until": "2026-10-01T12:00:00+00:00"}},
                "org_deactivated": False,
                "projected_at": "2026-09-22T12:00:00+00:00",
            },
        )

    def test_deactivated_org_limits_every_bucket_without_an_end(self):
        blob = build_quota_blob(42, {}, False, _NOW)
        assert blob is not None
        self.assertTrue(blob["org_deactivated"])
        self.assertEqual(
            blob["buckets"],
            {
                "ai_credits": {"limited": True, "limited_until": None},
                "posthog_code_credits": {"limited": True, "limited_until": None},
            },
        )

    def test_ttl_runs_past_the_latest_limit_end(self):
        soon = (_NOW + timedelta(hours=1)).timestamp()
        later = (_NOW + timedelta(days=2)).timestamp()
        blob = build_quota_blob(42, {"ai_credits": soon, "posthog_code_credits": later}, True, _NOW)
        assert blob is not None
        self.assertEqual(quota_blob_ttl(blob, _NOW), 2 * 24 * 3600 + LLM_GATEWAY_QUOTA_TTL_MARGIN_SECONDS)

    def test_ttl_for_a_deactivated_org_is_the_fixed_window(self):
        blob = build_quota_blob(42, {}, False, _NOW)
        assert blob is not None
        self.assertEqual(quota_blob_ttl(blob, _NOW), LLM_GATEWAY_QUOTA_DEACTIVATED_TTL)
        self.assertEqual(LLM_GATEWAY_QUOTA_DEACTIVATED_TTL, 30 * 24 * 3600)


@patch("posthog.storage.team_llm_gateway_quota_cache.settings")
class TestProjectTeamQuota(QuotaProjectionTestMixin):
    def _enable(self, mock_settings) -> None:
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL

    def test_ttl_remaining_reads_the_key_the_cache_writes(self, mock_settings):
        client = get_client(hypercache.redis_url)
        key = hypercache.cache_client.make_key(hypercache.get_cache_key(self.team))
        client.delete(key)
        self.assertIsNone(quota_blob_ttl_remaining(self.team))
        client.set(key, b"blob", ex=300)
        try:
            remaining = quota_blob_ttl_remaining(self.team)
        finally:
            client.delete(key)
        assert remaining is not None
        self.assertAlmostEqual(remaining, 300, delta=5)

    def test_deactivated_org_projects_every_team_with_the_fixed_ttl(self, mock_settings):
        self._enable(mock_settings)
        child = Team.objects.create(organization=self.organization, name="child env", parent_team=self.team)
        self.organization.is_active = False
        self.organization.save()
        with patch.object(hypercache, "set_cache_value_redis_only", wraps=hypercache.set_cache_value_redis_only) as w:
            written = project_org_quota(self.organization)
        self.assertEqual(written, 2)
        self.assertEqual({c.kwargs["ttl"] for c in w.call_args_list}, {LLM_GATEWAY_QUOTA_DEACTIVATED_TTL})
        for team in (self.team, child):
            blob = get_team_quota_blob(team)
            assert blob is not None, team.id
            self.assertTrue(blob["org_deactivated"])
            self.assertEqual(blob["buckets"]["posthog_code_credits"], {"limited": True, "limited_until": None})

    def test_noop_without_gateway_redis_url(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = None
        self.organization.is_active = False
        self.organization.save()
        self.assertIsNone(project_team_quota(self.team))
        self.assertIsNone(get_team_quota_blob(self.team))
        self.assertEqual(reconcile_quota_projection(), {"candidates": 0, "written": 0, "cleared": 0, "failed": 0})

    def test_redis_failure_is_captured_not_raised(self, mock_settings):
        self._enable(mock_settings)
        self.organization.is_active = False
        self.organization.save()
        with (
            patch.object(hypercache, "set_cache_value_redis_only", side_effect=ConnectionError("redis down")),
            patch("posthog.storage.team_llm_gateway_quota_cache.capture_exception") as capture,
        ):
            self.assertIsNone(project_team_quota(self.team))
        capture.assert_called_once()

    def test_batches_are_bounded_and_every_team_is_projected(self, mock_settings):
        self._enable(mock_settings)
        teams = [self.team] + [Team.objects.create(organization=self.organization, name=f"b{i}") for i in range(4)]
        self.organization.is_active = False
        self.organization.save()

        with (
            patch.object(quota_cache, "_BATCH_SIZE", 2),
            patch.object(quota_cache, "_derive_blobs", wraps=quota_cache._derive_blobs) as derive,
        ):
            self.assertEqual(project_org_quota(self.organization), 5)
        self.assertLessEqual(max(len(call.args[0]) for call in derive.call_args_list), 2)
        for team in teams:
            self.assertIsNotNone(get_team_quota_blob(team), team.id)

    def test_state_that_never_settles_gives_up_after_three_writes(self, mock_settings):
        self._enable(mock_settings)
        flips = iter(range(100))

        def flipping(teams, now):
            active = next(flips) % 2 == 1
            return {team.id: build_quota_blob(team.id, {}, active, now) for team in teams}

        with (
            patch("posthog.storage.team_llm_gateway_quota_cache._derive_blobs", side_effect=flipping),
            patch.object(hypercache, "delete_cache_entry", wraps=hypercache.delete_cache_entry) as deletes,
            patch.object(hypercache, "set_cache_value_redis_only", wraps=hypercache.set_cache_value_redis_only) as sets,
        ):
            project_team_quota(self.team)
        self.assertEqual(deletes.call_count + sets.call_count, 3)

    def test_a_failed_batch_read_is_not_retried_team_by_team(self, mock_settings):
        self._enable(mock_settings)
        teams = [self.team] + [Team.objects.create(organization=self.organization, name=f"f{i}") for i in range(3)]

        with (
            patch.object(quota_cache, "_derive_blobs", side_effect=ConnectionError("store down")) as derive,
            patch("posthog.storage.team_llm_gateway_quota_cache.capture_exception") as capture,
        ):
            self.assertEqual(project_org_quota(self.organization), 0)
        derive.assert_called_once()
        self.assertEqual(len(derive.call_args.args[0]), len(teams))
        capture.assert_called_once()

    def test_reachability_is_read_only_for_the_batch_teams(self, mock_settings):
        self._enable(mock_settings)
        self.organization.is_active = False
        self.organization.save()
        with CaptureQueriesContext(connection) as queries:
            project_team_quota(self.team)
        reach = [q["sql"] for q in queries.captured_queries if "posthog_projectsecretapikey" in q["sql"]]
        self.assertTrue(reach)
        for sql in reach:
            self.assertIn(f'"posthog_team"."id" IN ({self.team.id})', sql)


@patch("posthog.storage.team_llm_gateway_quota_cache.settings")
class TestReconcileQuotaProjection(QuotaProjectionTestMixin):
    def test_reconcile_reads_one_key_per_command(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        # A reachable deactivated org with no blob is the path that checks blob presence.
        Organization.objects.filter(pk=self.organization.pk).update(is_active=False)
        with patch.object(
            hypercache.cache_client, "get_many", side_effect=RuntimeError("CROSSSLOT Keys in request don't hash")
        ):
            reconcile_quota_projection()
        blob = get_team_quota_blob(self.team)
        assert blob is not None
        self.assertTrue(blob["org_deactivated"])

    def test_reconcile_restamps_a_deactivated_org_that_carries_a_blob(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        self.organization.is_active = False
        self.organization.save()
        project_org_quota(self.organization)
        self.assertIn(self.team.id, projected_team_ids())

        # A fresh deactivated blob is left alone; one inside the re-stamp window is rewritten.
        self.assertEqual(reconcile_quota_projection()["candidates"], 0)
        get_client(hypercache.redis_url).zadd(
            "llm_gateway_quota_cache_expiry", {str(self.team.id): int(timezone.now().timestamp()) + 3600}
        )
        counts = reconcile_quota_projection()
        self.assertEqual(counts["written"], 1)
        blob = get_team_quota_blob(self.team)
        assert blob is not None
        self.assertTrue(blob["org_deactivated"])
        self.assertEqual(reconcile_quota_projection()["candidates"], 0)

    def test_reconcile_rewrites_an_evicted_deactivated_blob_whose_tracking_survived(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        self.organization.is_active = False
        self.organization.save()
        project_org_quota(self.organization)
        hypercache.cache_client.delete(hypercache.get_cache_key(self.team))
        self.assertIn(self.team.id, projected_team_ids())
        self.assertIsNone(get_team_quota_blob(self.team))

        reconcile_quota_projection()
        blob = get_team_quota_blob(self.team)
        assert blob is not None
        self.assertTrue(blob["org_deactivated"])

    def test_reconcile_derives_a_deactivated_org_with_no_blob_from_postgres(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        Organization.objects.filter(pk=self.organization.pk).update(is_active=False)
        self.assertNotIn(self.team.id, projected_team_ids())

        reconcile_quota_projection()
        blob = get_team_quota_blob(self.team)
        assert blob is not None
        self.assertTrue(blob["org_deactivated"])

    def _deactivate_long_ago(self) -> None:
        Organization.objects.filter(pk=self.organization.pk).update(
            is_active=False, updated_at=timezone.now() - timedelta(seconds=LLM_GATEWAY_QUOTA_DEACTIVATED_TTL + 60)
        )

    def test_a_long_deactivated_org_with_no_gateway_credential_loses_its_blob(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        self.organization.is_active = False
        self.organization.save()
        project_org_quota(self.organization)
        self.assertIsNotNone(get_team_quota_blob(self.team))
        self._deactivate_long_ago()

        reconcile_quota_projection()
        self.assertIsNone(get_team_quota_blob(self.team))
        self.assertNotIn(self.team.id, projected_team_ids())
        self.assertEqual(reconcile_quota_projection()["candidates"], 0)
        self.assertIsNone(get_team_quota_blob(self.team))

    @parameterized.expand(["admission_enabled", "secret_key_on_child_env", "oauth_app"])
    def test_a_long_deactivated_org_that_can_still_reach_the_gateway_keeps_its_blob(self, mock_settings, credential):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        if credential == "admission_enabled":
            Team.objects.filter(pk=self.team.pk).update(llm_gateway_enabled_at=timezone.now())
        elif credential == "secret_key_on_child_env":
            child = Team.objects.create(organization=self.organization, name="child env", parent_team=self.team)
            ProjectSecretAPIKey.objects.create(
                team=child, label="gateway", scopes=["llm_gateway:read"], secure_value="sha256$quota-test"
            )
        else:
            OAuthApplication.objects.create(
                name="An app",
                client_type=OAuthApplication.CLIENT_CONFIDENTIAL,
                authorization_grant_type=OAuthApplication.GRANT_AUTHORIZATION_CODE,
                redirect_uris="https://example.com/callback",
                algorithm="RS256",
                organization=self.organization,
                user=self.user,
            )
        self._deactivate_long_ago()

        reconcile_quota_projection()
        blob = get_team_quota_blob(self.team)
        assert blob is not None
        self.assertTrue(blob["org_deactivated"])

    def test_a_revoked_admission_does_not_keep_a_long_deactivated_blob(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        Team.objects.filter(pk=self.team.pk).update(
            llm_gateway_enabled_at=timezone.now(), llm_gateway_revoked_at=timezone.now()
        )
        ProjectSecretAPIKey.objects.create(
            team=self.team, label="not gateway", scopes=["query:read"], secure_value="sha256$quota-test-2"
        )
        self._deactivate_long_ago()
        reconcile_quota_projection()
        self.assertIsNone(get_team_quota_blob(self.team))

    def test_reconcile_untracks_a_deleted_team_once_its_blob_expired(self, mock_settings):
        mock_settings.AI_GATEWAY_REDIS_URL = _GATEWAY_REDIS_URL
        client = get_client(hypercache.redis_url)
        now = int(timezone.now().timestamp())
        client.zadd(LLM_GATEWAY_QUOTA_CACHE_EXPIRY_SORTED_SET, {"987654321": now - 10, "987654322": now + 3600})
        reconcile_quota_projection()
        self.assertEqual(projected_team_ids(), {987654322})
