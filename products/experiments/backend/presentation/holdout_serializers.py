from typing import Any

from rest_framework import serializers

from posthog.api.shared import UserBasicSerializer

from products.experiments.backend.metric_utils import refresh_action_names_in_metric
from products.experiments.backend.models.experiment import ExperimentHoldout, ExperimentToSavedMetric


class ExperimentHoldoutSerializer(serializers.ModelSerializer):
    """A holdout group, a stable slice of users excluded from experiment exposure."""

    created_by = UserBasicSerializer(read_only=True)
    filters = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text=(
            "List of release-condition groups that define the held-out population, in the same shape as "
            "feature flag release conditions. The `rollout_percentage` of the first group is the exclusion "
            "percentage."
        ),
    )

    class Meta:
        model = ExperimentHoldout
        fields = ["id", "name", "description", "filters", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
        extra_kwargs = {
            "name": {"help_text": "Human-readable name for the holdout group."},
            "description": {"help_text": "Optional description of what this holdout reserves and why."},
            "created_at": {"help_text": "When the holdout was created."},
            "updated_at": {"help_text": "When the holdout was last changed."},
        }


class ExperimentToSavedMetricSerializer(serializers.ModelSerializer):
    """The link between an experiment and a shared (saved) metric."""

    query = serializers.JSONField(
        source="saved_metric.query",
        read_only=True,
        help_text="The metric definition stored on the shared metric.",
    )
    name = serializers.CharField(
        source="saved_metric.name",
        read_only=True,
        help_text="Name of the shared metric.",
    )

    class Meta:
        model = ExperimentToSavedMetric
        fields = ["id", "experiment", "saved_metric", "metadata", "created_at", "query", "name"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "experiment": {"help_text": "ID of the experiment the shared metric is attached to."},
            "saved_metric": {"help_text": "ID of the shared metric."},
            "metadata": {
                "help_text": (
                    "Per-experiment settings for the shared metric, such as `type` (primary or secondary) "
                    "and metric overrides."
                )
            },
            "created_at": {"help_text": "When the shared metric was attached to the experiment."},
        }

    def to_representation(self, instance: ExperimentToSavedMetric) -> dict[str, Any]:
        data = super().to_representation(instance)
        # Show current action names instead of the names cached when the metric was saved.
        if data.get("query"):
            refreshed = refresh_action_names_in_metric(data["query"], instance.saved_metric.team)
            if refreshed:
                data["query"] = refreshed
        return data
