from datetime import datetime

from posthog.test.base import APIBaseTest
from unittest.mock import MagicMock, patch

from django.test import override_settings

from parameterized import parameterized
from rest_framework import status

from posthog.models import Organization, OrganizationMembership, Team

from products.tasks.backend.access import (
    DESKTOP_SIGNUP_GATE_FLAG,
    DesktopAccessResolutionError,
    get_desktop_access_decision,
)
from products.tasks.backend.logic.services.code_usage_gate import code_access_required_response


class TestDesktopAccessPolicy(APIBaseTest):
    def setUp(self) -> None:
        super().setUp()
        self.feature_flag_patcher = patch("products.tasks.backend.access.get_feature_flag_or_none")
        self.mock_feature_flag = self.feature_flag_patcher.start()

        def feature_flag_value(*_args: object, **_kwargs: object) -> bool:
            return False

        self.mock_feature_flag.side_effect = feature_flag_value

    def tearDown(self) -> None:
        self.feature_flag_patcher.stop()
        super().tearDown()

    @override_settings(DEBUG=True)
    def test_debug_mode_allows_access_without_external_resolution(self) -> None:
        decision = get_desktop_access_decision(self.user, self.organization)

        self.assertTrue(decision.allowed)
        self.mock_feature_flag.assert_not_called()

    def test_access_is_allowed_without_billing_information(self) -> None:
        decision = get_desktop_access_decision(self.user, self.organization)

        self.assertTrue(decision.allowed)
        self.assertIsNone(decision.reason)

    @override_settings(DESKTOP_SIGNUP_CUTOFF="2000-01-01T00:00:00+00:00")
    def test_override_grants_access_despite_the_signup_gate(self) -> None:
        self.mock_feature_flag.side_effect = [True]

        decision = get_desktop_access_decision(self.user, self.organization)

        self.assertTrue(decision.allowed)

    @parameterized.expand(
        [
            ("joined_before_cutoff", "2026-10-02T00:00:00+00:00", "2026-10-01T23:59:59+00:00", True, True),
            ("joined_at_cutoff", "2026-10-02T00:00:00+00:00", "2026-10-02T00:00:00+00:00", True, False),
            ("naive_cutoff_reads_as_utc", "2026-10-02T00:00:00", "2026-10-02T00:00:01+00:00", True, False),
            ("cutoff_unset", "", "2026-10-03T00:00:00+00:00", True, True),
            ("gate_flag_off", "2026-10-02T00:00:00+00:00", "2026-10-03T00:00:00+00:00", False, True),
        ]
    )
    def test_signup_cutoff_blocks_new_users_without_a_reason(
        self,
        _name: str,
        cutoff: str,
        date_joined: str,
        gate_flag_enabled: bool,
        expected_allowed: bool,
    ) -> None:
        self.mock_feature_flag.side_effect = lambda key, *_args, **_kwargs: (
            gate_flag_enabled if key == "posthog-desktop-signup-gate" else False
        )
        self.user.date_joined = datetime.fromisoformat(date_joined)
        self.user.save(update_fields=["date_joined"])

        with override_settings(DESKTOP_SIGNUP_CUTOFF=cutoff):
            response = self.client.get(f"/api/projects/{self.team.id}/desktop/access/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"allowed": expected_allowed, "reason": None})

    @patch(
        "products.tasks.backend.logic.services.code_usage_gate.get_desktop_access_decision",
        side_effect=DesktopAccessResolutionError("unavailable"),
    )
    @patch("products.tasks.backend.logic.services.code_usage_gate.get_authenticator_scopes", return_value=[])
    def test_compute_gate_fails_closed_on_resolution_error(self, _mock_scopes, _mock_decision) -> None:
        response = code_access_required_response(MagicMock(), self.organization)

        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["code"], "desktop_access_unavailable")

    @parameterized.expand([(None,), ("control",), ("false",)])
    @override_settings(DESKTOP_SIGNUP_CUTOFF="2000-01-01T00:00:00+00:00")
    def test_indeterminate_flags_fail_closed(self, flag_value) -> None:
        for flag_values in ([flag_value], [False, flag_value]):
            self.mock_feature_flag.side_effect = flag_values
            with self.assertRaises(DesktopAccessResolutionError):
                get_desktop_access_decision(self.user, self.organization)

    @patch("products.tasks.backend.presentation.views.api.tasks_access.has_loops_access", return_value=True)
    def test_legacy_endpoint_grants_access(self, _mock_loops) -> None:
        response = self.client.get("/api/code/invites/check-access/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"has_access": True, "has_loops_access": True})

    @override_settings(DESKTOP_SIGNUP_CUTOFF="2000-01-01T00:00:00+00:00")
    def test_project_endpoint_is_scoped_to_each_organization(self) -> None:
        other_organization = Organization.objects.create(name="Other organization")
        other_team = Team.objects.create(organization=other_organization, name="Other project")
        OrganizationMembership.objects.create(
            organization=other_organization,
            user=self.user,
            level=OrganizationMembership.Level.MEMBER,
        )

        def gate_paused_for_the_first_organization(key: str, _distinct_id: str, *_args, **kwargs) -> bool:
            return key == DESKTOP_SIGNUP_GATE_FLAG and kwargs["groups"]["organization"] == str(self.organization.id)

        self.mock_feature_flag.side_effect = gate_paused_for_the_first_organization

        paused_response = self.client.get(f"/api/projects/{self.team.id}/desktop/access/")
        allowed_response = self.client.get(f"/api/projects/{other_team.id}/desktop/access/")

        self.assertEqual(paused_response.status_code, status.HTTP_200_OK)
        self.assertEqual(paused_response.json(), {"allowed": False, "reason": None})
        self.assertEqual(allowed_response.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed_response.json(), {"allowed": True, "reason": None})

    @patch(
        "products.tasks.backend.presentation.views.desktop_access.get_desktop_access_decision",
        side_effect=DesktopAccessResolutionError,
    )
    def test_project_endpoint_returns_retryable_service_error(self, _mock_decision) -> None:
        response = self.client.get(f"/api/projects/{self.team.id}/desktop/access/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.json()["code"], "desktop_access_unavailable")
