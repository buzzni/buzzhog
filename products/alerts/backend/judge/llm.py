"""A series judge that asks a model instead of fitting a statistical test.

The point is a "just watch this for anything odd" option that needs no statistical
model and no threshold, and that can honor instructions the statistical detectors
cannot express ("only care about drops", "ignore the weekend dip").

One model call per check. The model sees the recent series as a table, a chart of the
same points, a plain-English description of what the insight measures, and the alert
author's own notes on what counts as strange.
"""

from typing import Any

import numpy as np
import structlog

from posthog.tasks.alerts.detector import LLM_DETECTOR_DEFAULT_WINDOW, LLM_DETECTOR_MIN_POINTS

from products.alerts.backend.judge.contract import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    MAX_PROMPT_POINTS,
    JudgeAttribution,
    LLMDetectorMisconfiguredError,
    LLMDetectorUnavailableError,
    SeriesContext,
    SeriesJudgment,
)
from products.alerts.backend.judge.verdict import LLMDetectionVerdict
from products.alerts.backend.llm_detector_limits import llm_detector_access_error

logger = structlog.get_logger(__name__)

DEFAULT_WINDOW = LLM_DETECTOR_DEFAULT_WINDOW


def prompt_window(config: dict[str, Any]) -> int:
    """How many trailing points the model is shown for this configuration."""
    return min(int(config.get("window") or DEFAULT_WINDOW), MAX_PROMPT_POINTS)


MIN_POINTS_TO_JUDGE = LLM_DETECTOR_MIN_POINTS

# Recorded on each verdict so a stored check names the model that judged it.
LLM_DETECTOR_MODEL = "claude-haiku-5-5"

# The rationale is appended to the breach text that every destination renders. Discord
# rejects a message over 2,000 characters, and the breach prefix and the other breaches in
# the same message need room too.
MAX_RATIONALE_CHARS = 600


class LLMSeriesJudge:
    """Config:
    instructions: str - the author's description of what counts as unusual (optional)
    threshold: float - minimum reported confidence before the alert fires (default: 0.7)
    window: int - how many recent points the model is shown (default: 90)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def judge_latest(
        self, data: np.ndarray, *, series: SeriesContext, attribution: JudgeAttribution
    ) -> SeriesJudgment | None:
        return self._judge(data, series=series, attribution=attribution, judge_every_point=False)

    def judge_every_point(
        self, data: np.ndarray, *, series: SeriesContext, attribution: JudgeAttribution
    ) -> SeriesJudgment | None:
        return self._judge(data, series=series, attribution=attribution, judge_every_point=True)

    def _judge(
        self, data: np.ndarray, *, series: SeriesContext, attribution: JudgeAttribution, judge_every_point: bool
    ) -> SeriesJudgment | None:
        if len(data) < MIN_POINTS_TO_JUDGE:
            return None

        window = prompt_window(self.config)
        verdict = self._ask_model(
            data=data, series=series, attribution=attribution, window=window, judge_every_point=judge_every_point
        )
        return self._judgment(verdict, data=data, window=window, judge_every_point=judge_every_point)

    def _ask_model(
        self,
        *,
        data: np.ndarray,
        series: SeriesContext,
        attribution: JudgeAttribution,
        window: int,
        judge_every_point: bool,
    ) -> LLMDetectionVerdict:
        # An alert created while the organization was in the rollout and had consent on keeps
        # being checked after either is withdrawn. Refusing here covers every path to the
        # model, scheduled or previewed, so the flag is a real stop on spend.
        access_error = llm_detector_access_error(
            distinct_id=str(attribution.user.distinct_id), organization=attribution.team.organization
        )
        if access_error:
            raise LLMDetectorMisconfiguredError(
                f"{access_error} This alert cannot be checked until that changes. Switch it to a statistical "
                "detector to keep it running."
            )

        raise LLMDetectorUnavailableError("The AI detector is not available on this installation.")

    def _judgment(
        self, verdict: LLMDetectionVerdict, *, data: np.ndarray, window: int, judge_every_point: bool
    ) -> SeriesJudgment:
        configured_threshold = self.config.get("threshold")
        threshold = float(configured_threshold if configured_threshold is not None else DEFAULT_CONFIDENCE_THRESHOLD)
        confident = verdict.confidence >= threshold
        fires = verdict.is_anomaly and confident

        index_offset = max(0, len(data) - window)
        reported_indices = [index + index_offset for index in verdict.triggered_indices]
        score_indices = self._clamp_indices(reported_indices, length=len(data)) if verdict.is_anomaly else []
        indices = score_indices
        latest_point_flagged = (len(data) - 1) in indices
        if not judge_every_point:
            # A live check judges one point. The prompt asks the model to list the final index
            # when, and only when, that point is the anomaly, so a verdict that flags only
            # history (or nothing) must not page anyone about a normal current value.
            fires = fires and latest_point_flagged
            indices = [len(data) - 1] if fires else []
        elif not fires:
            indices = []

        anomaly_score = self._anomaly_score(verdict)
        return SeriesJudgment(
            fires=fires,
            verdict_is_anomaly=verdict.is_anomaly,
            confidence=verdict.confidence,
            kind=verdict.kind,
            rationale=verdict.rationale[:MAX_RATIONALE_CHARS],
            model=LLM_DETECTOR_MODEL,
            score=anomaly_score,
            triggered_indices=tuple(indices),
            all_scores=self._scores(anomaly_score, indices=score_indices, length=len(data))
            if judge_every_point
            else (anomaly_score,),
            below_threshold=verdict.is_anomaly and not confident,
            latest_point_not_flagged=verdict.is_anomaly and not judge_every_point and not latest_point_flagged,
        )

    @staticmethod
    def _anomaly_score(verdict: LLMDetectionVerdict) -> float:
        """The verdict on the scale the threshold gate and the check history chart read scores on.

        The model reports confidence in its verdict, whichever way it went. A confident "no
        anomaly" is a low anomaly score; stored raw, it would plot above the threshold as a
        check that would have fired.
        """
        return verdict.confidence if verdict.is_anomaly else 1.0 - verdict.confidence

    @staticmethod
    def _clamp_indices(indices: list[int], *, length: int) -> list[int]:
        """Drop indices the model invented outside the series, and de-duplicate."""
        return sorted({index for index in indices if 0 <= index < length})

    @staticmethod
    def _scores(confidence: float, *, indices: list[int], length: int) -> tuple[float | None, ...]:
        """One score per point for the simulation chart.

        The model reports a single confidence for the whole judgment rather than a score
        per point, so only the points it flagged carry one. The rest are left unscored
        instead of being given a made-up number.
        """
        flagged = set(indices)
        return tuple(confidence if index in flagged else None for index in range(length))
