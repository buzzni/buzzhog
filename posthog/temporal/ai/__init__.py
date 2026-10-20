from posthog.temporal.ai.anomaly_investigation import AnomalyInvestigationWorkflow, investigate_anomaly_activity

AI_WORKFLOWS = [
    AnomalyInvestigationWorkflow,
]

AI_ACTIVITIES = [
    investigate_anomaly_activity,
]
