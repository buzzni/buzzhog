from temporalio import activity

from products.slack_app.backend.temporal.types import PostHogCodeSlackMentionWorkflowInputs


@activity.defn
def enforce_posthog_code_billing_quota_activity(
    inputs: PostHogCodeSlackMentionWorkflowInputs,
    channel: str,
    thread_ts: str,
    slack_user_id: str,
) -> bool:
    """Return True when the workflow must stop because the team is over its AI credits quota.

    A self-hosted install has no billing, so no team is over quota. The activity stays as the
    workflow's first step so workflow histories keep the same activity sequence.
    """
    return False
