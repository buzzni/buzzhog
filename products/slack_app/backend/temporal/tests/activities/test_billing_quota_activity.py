from django.test import SimpleTestCase

from products.slack_app.backend.temporal import (
    PostHogCodeSlackMentionWorkflowInputs,
    enforce_posthog_code_billing_quota_activity,
)


class TestEnforcePostHogCodeBillingQuotaActivity(SimpleTestCase):
    def test_no_turn_is_blocked_without_billing(self):
        inputs = PostHogCodeSlackMentionWorkflowInputs(event={}, integration_id=1, slack_team_id="T_SLACK", user_id=1)
        assert enforce_posthog_code_billing_quota_activity(inputs, "C001", "1000.0000", "U_BOB") is False
