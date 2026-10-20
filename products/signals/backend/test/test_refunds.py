import json
from datetime import UTC, datetime

import time_machine
from posthog.test.base import APIBaseTest, BaseTest
from unittest.mock import patch

from django.core.management import CommandError, call_command

from parameterized import parameterized
from rest_framework import status

from posthog.models import Organization, Team

from products.signals.backend.billing import SIGNALS_CREDITS_PER_REPORT_WITH_PR
from products.signals.backend.models import SignalReport, SignalReportArtefact, SignalReportRefund
from products.signals.backend.quota import SELF_DRIVING_QUOTA_ENFORCEMENT_FLAG
from products.signals.backend.test.test_billing import _make_pr_run, _make_report

_PERIOD = ["2026-06-01T00:00:00Z", "2026-07-01T00:00:00Z"]
_NOW = "2026-06-15T12:00:00Z"


def _make_refund(
    report: SignalReport,
    *,
    billing_path: str = SignalReportRefund.BillingPath.CREDITED,
    pr_run_created_at: datetime | None = None,
    # None models a row created before the frozen period bounds existed.
    period: tuple[datetime, datetime] | None = (
        datetime(2026, 6, 1, tzinfo=UTC),
        datetime(2026, 7, 1, tzinfo=UTC),
    ),
) -> SignalReportRefund:
    return SignalReportRefund.objects.create(
        team=report.team,
        report=report,
        reason=SignalReportRefund.Reason.PR_INCORRECT,
        billing_path=billing_path,
        credits=SIGNALS_CREDITS_PER_REPORT_WITH_PR,
        pr_url="https://github.com/x/y/pull/1",
        pr_run_created_at=pr_run_created_at or datetime(2026, 6, 10, tzinfo=UTC),
        period_start=period[0] if period else None,
        period_end=period[1] if period else None,
    )


@patch("posthoganalytics.feature_enabled", return_value=True)
class TestSignalReportRefundAPI(APIBaseTest):
    def setUp(self):
        super().setUp()
        self.organization.usage = {"period": _PERIOD}
        self.organization.save()

    def _refund_url(self, report_id: str) -> str:
        return f"/api/projects/{self.team.id}/signals/reports/{report_id}/refund/"

    def _state_url(self, report_id: str) -> str:
        return f"/api/projects/{self.team.id}/signals/reports/{report_id}/state/"

    def _report_with_pr(
        self, *, pr_created_at: datetime, report_status: str = SignalReport.Status.READY
    ) -> SignalReport:
        report = _make_report(self.team, status=report_status)
        _make_pr_run(self.team, report, created_at=pr_created_at)
        return report

    def _refund(self, report: SignalReport, body: dict | None = None):
        return self.client.post(self._refund_url(str(report.id)), body or {"reason": "pr_not_useful"}, format="json")

    @time_machine.travel(_NOW, tick=False)
    def test_refund_earlier_in_period_goes_credited_and_archives(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, 9, 30, tzinfo=UTC))
        response = self._refund(report, {"reason": "pr_incorrect", "note": "does not fix the bug"})

        assert response.status_code == status.HTTP_200_OK, response.json()
        body = response.json()
        assert body["billing_path"] == "credited"
        assert body["credits"] == 1500
        assert body["reason"] == "pr_incorrect"
        assert body["pr_url"] == "https://github.com/x/y/pull/1"
        assert body["already_refunded"] is False
        assert body["billing_synced"] is False
        assert body["credit_amount_usd"] is None

        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED
        refund = report.refund
        assert refund.billing_path == SignalReportRefund.BillingPath.CREDITED
        assert refund.pr_run_created_at == datetime(2026, 6, 10, 9, 30, tzinfo=UTC)
        # The accepted billing period is frozen on the row — the sync payload reports these
        # bounds, so a sync landing after rollover still credits the right period.
        assert refund.period_start == datetime(2026, 6, 1, tzinfo=UTC)
        assert refund.period_end == datetime(2026, 7, 1, tzinfo=UTC)
        assert refund.created_by_id == self.user.id
        assert refund.note == "does not fix the bug"

        dismissal = SignalReportArtefact.objects.get(report=report, type=SignalReportArtefact.ArtefactType.DISMISSAL)
        content = json.loads(dismissal.content)
        assert content["reason"] == "refunded"
        assert content["note"] == "does not fix the bug"

    @time_machine.travel(_NOW, tick=False)
    def test_refund_on_pr_run_day_goes_excluded(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 15, 8, 0, tzinfo=UTC))
        response = self._refund(report)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["billing_path"] == "excluded"

    @time_machine.travel("2026-06-15T00:30:00Z", tick=False)
    def test_refund_just_after_utc_midnight_goes_credited(self, _flag):
        # The path rule is the PR run's UTC day, not "before the 03:45 send" — a 23:50 PR refunded
        # at 00:30 must go credited even though the usage report hasn't shipped yet.
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 14, 23, 50, tzinfo=UTC))
        response = self._refund(report)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["billing_path"] == "credited"

    @time_machine.travel(_NOW, tick=False)
    def test_refund_without_billable_pr_is_rejected(self, _flag):
        report = _make_report(self.team)
        response = self._refund(report)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no billable implementation PR" in response.json()["error"]

    @time_machine.travel(_NOW, tick=False)
    def test_refund_for_previous_period_pr_is_rejected(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 5, 20, tzinfo=UTC))
        response = self._refund(report)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "previous billing period" in response.json()["error"]

    @parameterized.expand(
        [
            ("pr_in_current_month", datetime(2026, 6, 10, tzinfo=UTC), status.HTTP_200_OK),
            ("pr_in_previous_month", datetime(2026, 5, 20, tzinfo=UTC), status.HTTP_400_BAD_REQUEST),
        ]
    )
    @time_machine.travel(_NOW, tick=False)
    def test_missing_billing_period_falls_back_to_calendar_month(self, _flag, _name, pr_created_at, expected_status):
        self.organization.usage = None
        self.organization.save()
        report = self._report_with_pr(pr_created_at=pr_created_at)
        response = self._refund(report)
        assert response.status_code == expected_status

    @parameterized.expand(
        [
            ("eligible", None),
            ("out_of_period", "out_of_period"),
            ("no_billable_pr", "no_billable_pr"),
            ("already_refunded", "already_refunded"),
            ("billing_exempt", "billing_exempt"),
        ]
    )
    @time_machine.travel(_NOW, tick=False)
    def test_report_response_carries_refund_ineligibility_reason(self, _flag, case, expected):
        # The serializer field shares the refund endpoint's eligibility decision (billable moment +
        # period context + helper); a wiring regression would re-enable buttons that only 400.
        # The list resolves the billable moment from a batched map and the detail from a per-row
        # annotation, so both paths are asserted — the inbox reads the list one.
        if case == "no_billable_pr":
            report = _make_report(self.team)
        else:
            pr_at = datetime(2026, 5, 20, tzinfo=UTC) if case == "out_of_period" else datetime(2026, 6, 10, tzinfo=UTC)
            report = self._report_with_pr(pr_created_at=pr_at)
        if case == "already_refunded":
            _make_refund(report)
        if case == "billing_exempt":
            SignalReport.objects.filter(id=report.id).update(
                billing_exempt_reason=SignalReport.BillingExemptReason.POSTHOG_HEALTH_CHECK
            )

        response = self.client.get(f"/api/projects/{self.team.id}/signals/reports/{report.id}/")

        assert response.status_code == 200
        assert response.json()["refund_ineligibility_reason"] == expected

        list_response = self.client.get(f"/api/projects/{self.team.id}/signals/reports/")

        assert list_response.status_code == 200
        listed = {row["id"]: row for row in list_response.json()["results"]}
        assert listed[str(report.id)]["refund_ineligibility_reason"] == expected

    @time_machine.travel(_NOW, tick=False)
    def test_refund_on_exempt_report_is_rejected(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        SignalReport.objects.filter(id=report.id).update(
            billing_exempt_reason=SignalReport.BillingExemptReason.POSTHOG_HEALTH_CHECK
        )
        response = self._refund(report)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "never-billable" in response.json()["error"]

    @time_machine.travel(_NOW, tick=False)
    def test_second_refund_is_idempotent(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        first = self._refund(report, {"reason": "pr_incorrect"})
        second = self._refund(report, {"reason": "duplicate"})

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_200_OK
        assert second.json()["already_refunded"] is True
        # The original refund is returned unchanged — the second reason never sticks.
        assert second.json()["reason"] == "pr_incorrect"
        assert second.json()["id"] == first.json()["id"]
        assert SignalReportRefund.objects.filter(report=report).count() == 1

    @time_machine.travel(_NOW, tick=False)
    def test_refund_reaches_already_archived_report(self, _flag):
        # An archived-but-charged report must still be refundable (suppressed reports are hidden
        # from most by-id actions); it stays suppressed.
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        report.transition_to(SignalReport.Status.SUPPRESSED)
        report.save()
        response = self._refund(report)
        assert response.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED

    @parameterized.expand(
        [
            # A merged PR is a genuine terminal state — the work shipped — so refund leaves it RESOLVED.
            ("merged_pr", {"pr_url": "https://github.com/x/y/pull/1", "pr_merged": True}, SignalReport.Status.RESOLVED),
            # Resolved manually without a merged PR: refund must suppress it, otherwise the linked PR
            # is never closed and the caller keeps the implementation work after being refunded.
            ("resolved_without_merge", {"pr_url": "https://github.com/x/y/pull/1"}, SignalReport.Status.SUPPRESSED),
        ]
    )
    @time_machine.travel(_NOW, tick=False)
    def test_refund_of_resolved_report_suppresses_unless_pr_merged(self, _flag, _name, output, expected_status):
        report = _make_report(self.team, status=SignalReport.Status.RESOLVED)
        _make_pr_run(self.team, report, created_at=datetime(2026, 6, 10, tzinfo=UTC), output=output)
        response = self._refund(report)
        assert response.status_code == status.HTTP_200_OK, response.json()
        report.refresh_from_db()
        assert report.status == expected_status
        # The permanent marker lands regardless of whether the status changed.
        assert SignalReportArtefact.objects.filter(
            report=report, type=SignalReportArtefact.ArtefactType.DISMISSAL
        ).exists()

    @time_machine.travel(_NOW, tick=False)
    def test_invalid_reason_is_rejected(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        response = self._refund(report, {"reason": "because"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not SignalReportRefund.objects.filter(report=report).exists()

    @time_machine.travel(_NOW, tick=False)
    def test_refund_fires_analytics_event(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        with patch("products.signals.backend.views.report_user_action") as mock_report:
            self._refund(report)
        mock_report.assert_called_once()
        assert mock_report.call_args.args[1] == "signals_pr_refund_created"
        properties = mock_report.call_args.kwargs["properties"]
        assert properties["billing_path"] == "credited"
        assert properties["credits"] == 1500
        assert properties["pr_merged"] is False
        assert properties["days_since_pr"] == 5

    @parameterized.expand(
        [
            # A merged PR (output.pr_merged) reports pr_merged=True whatever the report status.
            (
                "merged_pr",
                SignalReport.Status.READY,
                {"pr_url": "https://github.com/x/y/pull/1", "pr_merged": True},
                True,
                None,
            ),
            ("canonical_merge", SignalReport.Status.READY, {"pr_url": "https://github.com/x/y/pull/1"}, True, "merged"),
            # Resolved without a merged PR must NOT report a merge: status alone can't attest one.
            (
                "resolved_without_merge",
                SignalReport.Status.RESOLVED,
                {"pr_url": "https://github.com/x/y/pull/1"},
                False,
                None,
            ),
        ]
    )
    @time_machine.travel(_NOW, tick=False)
    def test_analytics_pr_merged_reflects_merge_flag_not_status(
        self, _flag, _name, report_status, output, expected, linked_state
    ):
        report = _make_report(self.team, status=report_status)
        _make_pr_run(self.team, report, created_at=datetime(2026, 6, 10, tzinfo=UTC), output=output)
        if linked_state is not None:
            from products.signals.backend.models import SignalReportPullRequest

            assert (
                SignalReportPullRequest.objects.for_team(self.team.id)
                .filter(repository="x/y", number=1)
                .update(state=linked_state)
                == 1
            )
        with patch("products.signals.backend.views.report_user_action") as mock_report:
            assert self._refund(report).status_code == status.HTTP_200_OK
        assert mock_report.call_args.kwargs["properties"]["pr_merged"] is expected

    @time_machine.travel(_NOW, tick=False)
    def test_later_merged_pr_does_not_vouch_for_the_refunded_one(self, _flag):
        # The refund reverses the charge for the first billable PR, and it's that PR which must be
        # closed if it never merged. A different, later PR on the same report merging says nothing
        # about it — treating the report as merged would leave the refunded PR open.
        report = _make_report(self.team, status=SignalReport.Status.RESOLVED)
        _make_pr_run(
            self.team,
            report,
            created_at=datetime(2026, 6, 10, tzinfo=UTC),
            output={"pr_url": "https://github.com/x/y/pull/1"},
        )
        _make_pr_run(
            self.team,
            report,
            created_at=datetime(2026, 6, 12, tzinfo=UTC),
            output={"pr_url": "https://github.com/x/y/pull/2", "pr_merged": True},
        )

        with patch("products.signals.backend.views.report_user_action") as mock_report:
            assert self._refund(report).status_code == status.HTTP_200_OK

        assert mock_report.call_args.kwargs["properties"]["pr_merged"] is False
        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED

    @time_machine.travel(_NOW, tick=False)
    def test_merge_flag_on_non_github_run_does_not_attest_a_merge(self, _flag):
        # A billable GitHub run makes the report refundable, while a second implementation run
        # carries a merge flag on a URL the billing path never counts. That flag must not attest a
        # merge: if it did, the refund would leave the report resolved and its real PR unclosed.
        report = _make_report(self.team, status=SignalReport.Status.RESOLVED)
        _make_pr_run(
            self.team,
            report,
            created_at=datetime(2026, 6, 10, tzinfo=UTC),
            output={"pr_url": "https://github.com/x/y/pull/1"},
        )
        _make_pr_run(
            self.team,
            report,
            created_at=datetime(2026, 6, 11, tzinfo=UTC),
            output={"pr_url": "https://gitlab.example.com/x/y/-/merge_requests/1", "pr_merged": True},
        )

        with patch("products.signals.backend.views.report_user_action") as mock_report:
            assert self._refund(report).status_code == status.HTTP_200_OK

        assert mock_report.call_args.kwargs["properties"]["pr_merged"] is False
        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED

    @time_machine.travel(_NOW, tick=False)
    def test_restore_of_refunded_report_is_blocked(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        assert self._refund(report).status_code == status.HTTP_200_OK

        response = self.client.post(self._state_url(str(report.id)), {"state": "potential"}, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["error"] == "Refunded reports can't be restored."
        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED

    @time_machine.travel(_NOW, tick=False)
    def test_snooze_of_refunded_resolved_report_is_blocked(self, _flag):
        # A merged-PR report stays RESOLVED through its refund, so the guard can't key on SUPPRESSED:
        # snoozing it to POTENTIAL would put a refunded report back where grouping re-promotes it to
        # candidate, and later PR runs on it are never billable.
        report = _make_report(self.team, status=SignalReport.Status.RESOLVED)
        _make_pr_run(
            self.team,
            report,
            created_at=datetime(2026, 6, 10, tzinfo=UTC),
            output={"pr_url": "https://github.com/x/y/pull/1", "pr_merged": True},
        )
        assert self._refund(report).status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.status == SignalReport.Status.RESOLVED

        response = self.client.post(self._state_url(str(report.id)), {"state": "potential"}, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["error"] == "Refunded reports can't be restored."
        report.refresh_from_db()
        assert report.status == SignalReport.Status.RESOLVED

    @time_machine.travel(_NOW, tick=False)
    def test_resolve_of_refunded_report_is_blocked(self, _flag):
        # A refunded report is suppressed; resolving would undo that suppression — and the PR close
        # it triggers — so the refund guard must cover resolve too (not just restore to potential).
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        assert self._refund(report).status_code == status.HTTP_200_OK

        response = self.client.post(self._state_url(str(report.id)), {"state": "resolved"}, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["error"] == "Refunded reports can't be restored."
        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED

    @time_machine.travel(_NOW, tick=False)
    def test_resolve_then_refund_suppresses_report(self, _flag):
        # The exploit path the refund must close: a task:write caller resolves a ready report through
        # the API while its PR is still open, then refunds it. If the refund left it RESOLVED the
        # dismissal receiver would never close that PR, so the caller keeps the work and the money.
        # The refund must suppress it, and it must then be non-restorable.
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        resolve = self.client.post(self._state_url(str(report.id)), {"state": "resolved"}, format="json")
        assert resolve.status_code == status.HTTP_200_OK, resolve.json()

        assert self._refund(report).status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.status == SignalReport.Status.SUPPRESSED

        reopen = self.client.post(self._state_url(str(report.id)), {"state": "resolved"}, format="json")
        assert reopen.status_code == status.HTTP_409_CONFLICT

    @time_machine.travel(_NOW, tick=False)
    def test_bulk_restore_of_refunded_report_is_blocked(self, _flag):
        refunded = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        assert self._refund(refunded).status_code == status.HTTP_200_OK
        archived = _make_report(self.team)
        archived.transition_to(SignalReport.Status.SUPPRESSED)
        archived.save()

        response = self.client.post(
            f"/api/projects/{self.team.id}/signals/reports/bulk-state/",
            {"ids": [str(refunded.id), str(archived.id)], "state": "potential"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        results = {r["id"]: r for r in response.json()["results"]}
        assert results[str(refunded.id)]["outcome"] == "skipped"
        assert results[str(refunded.id)]["detail"] == "Refunded reports can't be restored."
        assert results[str(archived.id)]["outcome"] == "transitioned"
        refunded.refresh_from_db()
        assert refunded.status == SignalReport.Status.SUPPRESSED

    @time_machine.travel(_NOW, tick=False)
    def test_report_response_includes_refund_and_exemption_fields(self, _flag):
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        self._refund(report)
        response = self.client.get(f"/api/projects/{self.team.id}/signals/reports/{report.id}/")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["refund"]["billing_path"] == "credited"
        assert body["refund"]["reason"] == "pr_not_useful"
        assert body["billing_exempt_reason"] is None

    @time_machine.travel(_NOW, tick=False)
    def test_refund_summary_aggregates_credited_refunds_org_wide(self, _flag):
        # Two teams in the org contribute; excluded-path, out-of-period, and foreign-org refunds don't.
        report_a = self._report_with_pr(pr_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        _make_refund(report_a, pr_run_created_at=datetime(2026, 6, 10, tzinfo=UTC))
        sibling_team = Team.objects.create(organization=self.organization, name="sibling")
        report_b = _make_report(sibling_team)
        _make_refund(report_b, pr_run_created_at=datetime(2026, 6, 12, tzinfo=UTC))
        excluded = _make_report(self.team)
        _make_refund(
            excluded,
            billing_path=SignalReportRefund.BillingPath.EXCLUDED,
            pr_run_created_at=datetime(2026, 6, 13, tzinfo=UTC),
        )
        out_of_period = _make_report(self.team)
        _make_refund(out_of_period, pr_run_created_at=datetime(2026, 5, 20, tzinfo=UTC))
        other_org = Organization.objects.create(name="other")
        other_team = Team.objects.create(organization=other_org, name="other")
        foreign = _make_report(other_team)
        _make_pr_run(other_team, foreign, created_at=datetime(2026, 6, 14, tzinfo=UTC))
        _make_refund(foreign, pr_run_created_at=datetime(2026, 6, 14, tzinfo=UTC))

        response = self.client.get(f"/api/projects/{self.team.id}/signals/reports/refund-summary/")
        assert response.status_code == status.HTTP_200_OK
        # period_billable_credits: only report_a has a billable PR run in this org (credited
        # refunds stay counted — usage is truthful); the foreign org's billable PR must not leak in.
        assert response.json() == {
            "credited_refund_count": 2,
            "credited_credits": 3000,
            "period_billable_credits": 1500,
            "quota_limited": False,
        }

    @time_machine.travel(_NOW, tick=False)
    def test_refund_summary_counts_unreported_prs_live_until_excluded_refund(self, _flag):
        # A PR created today hasn't shipped to billing yet but must count in the live number,
        # and a same-day (excluded-path) refund must visibly un-count it.
        report = self._report_with_pr(pr_created_at=datetime(2026, 6, 15, 8, 0, tzinfo=UTC))
        url = f"/api/projects/{self.team.id}/signals/reports/refund-summary/"

        assert self.client.get(url).json()["period_billable_credits"] == 1500
        assert self._refund(report).json()["billing_path"] == "excluded"
        assert self.client.get(url).json()["period_billable_credits"] == 0

    @time_machine.travel(_NOW, tick=False)
    def test_refund_summary_reports_quota_limited_from_the_gate(self, _flag):
        # The widget's "agents are paused" banner keys off this field, so it must reflect the
        # same gate the pipeline enforces, not the widget's own usage math.
        from products.signals.backend.quota import SelfDrivingQuotaGate

        url = f"/api/projects/{self.team.id}/signals/reports/refund-summary/"
        with patch(
            "products.signals.backend.views.self_driving_quota_gate",
            return_value=SelfDrivingQuotaGate(limited=True, enforced=True),
        ):
            assert self.client.get(url).json()["quota_limited"] is True


class TestSignalReportRefundFlagGate(APIBaseTest):
    @patch("posthoganalytics.feature_enabled")
    def test_refund_summary_available_with_only_enforcement_flag(self, flag_mock):
        # The two flags roll out independently; an enforcement-only org still needs quota_limited
        # from this endpoint, or the widget's paused banner can never render.
        flag_mock.side_effect = lambda key, *args, **kwargs: key == SELF_DRIVING_QUOTA_ENFORCEMENT_FLAG
        summary = self.client.get(f"/api/projects/{self.team.id}/signals/reports/refund-summary/")
        assert summary.status_code == status.HTTP_200_OK
        assert summary.json()["quota_limited"] is False
        # The refund action itself stays refunds-gated.
        report = _make_report(self.team)
        refund = self.client.post(
            f"/api/projects/{self.team.id}/signals/reports/{report.id}/refund/", {"reason": "other"}, format="json"
        )
        assert refund.status_code == status.HTTP_404_NOT_FOUND

    @parameterized.expand([("refund",), ("refund_summary",)])
    @patch("posthoganalytics.feature_enabled", return_value=False)
    def test_endpoints_unavailable_with_flag_off(self, action_path, _flag):
        report = _make_report(self.team)
        if action_path == "refund":
            url = f"/api/projects/{self.team.id}/signals/reports/{report.id}/refund/"
            response = self.client.post(url, {"reason": "other"}, format="json")
        else:
            url = f"/api/projects/{self.team.id}/signals/reports/refund-summary/"
            response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not SignalReportRefund.objects.filter(report=report).exists()


class TestExemptSignalReportBillingCommand(BaseTest):
    def test_marks_report_exempt(self):
        report = _make_report(self.team)
        call_command("exempt_signal_report_billing", str(self.team.id), str(report.id), "posthog_system")
        report.refresh_from_db()
        assert report.billing_exempt_reason == SignalReport.BillingExemptReason.POSTHOG_SYSTEM

    def test_refuses_once_billable_pr_run_exists(self):
        report = _make_report(self.team)
        _make_pr_run(self.team, report, created_at=datetime(2026, 6, 10, tzinfo=UTC))
        with self.assertRaises(CommandError) as ctx:
            call_command("exempt_signal_report_billing", str(self.team.id), str(report.id), "posthog_system")
        assert "use a refund" in str(ctx.exception)
        report.refresh_from_db()
        assert report.billing_exempt_reason is None
