from typing import Any

AGENT_COMMAND_DISPATCHED_METHOD = "_posthog/agent_command_dispatched"
TURN_COMPLETE_METHOD = "_posthog/turn_complete"
BACKGROUND_TURN_COMPLETE_METHOD = "_posthog/background_turn_complete"
STOP_REASON_END_TURN = "end_turn"
STOP_REASON_IDLE_RESUME = "idle_resume"
PI_RUNTIME_ERROR_MESSAGE = "The Pi agent runtime reported an error and ended the turn."

_ACP_GENERATION_UPDATES = frozenset(
    {
        "agent_message",
        "agent_message_chunk",
        "agent_thought_chunk",
        "tool_call",
        "tool_call_update",
    }
)

_PI_GENERATION_EVENTS = frozenset(
    {
        "assistant_message_chunk",
        "assistant_thought_chunk",
        "tool_call_started",
        "tool_call_updated",
    }
)


def is_agent_command_dispatched(event: dict[str, Any]) -> bool:
    notification = event.get("notification")
    return (
        event.get("type") == "notification"
        and isinstance(notification, dict)
        and notification.get("method") == AGENT_COMMAND_DISPATCHED_METHOD
    )


def is_agent_generation_event(event: dict[str, Any]) -> bool:
    if event.get("type") == "pi_event":
        pi_event = event.get("event")
        return isinstance(pi_event, dict) and pi_event.get("type") in _PI_GENERATION_EVENTS

    notification = event.get("notification")
    if event.get("type") != "notification" or not isinstance(notification, dict):
        return False
    if notification.get("method") != "session/update":
        return False
    params = notification.get("params")
    if not isinstance(params, dict):
        return False
    update = params.get("update")
    return isinstance(update, dict) and update.get("sessionUpdate") in _ACP_GENERATION_UPDATES


def _notification_method(event: dict[str, Any]) -> str | None:
    notification = event.get("notification")
    if event.get("type") != "notification" or not isinstance(notification, dict):
        return None
    method = notification.get("method")
    return method if isinstance(method, str) else None


def _notification_params(event: dict[str, Any]) -> dict[str, Any]:
    notification = event.get("notification")
    if not isinstance(notification, dict):
        return {}
    params = notification.get("params")
    return params if isinstance(params, dict) else {}


def _pi_turn_completed(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("type") != "pi_event":
        return None
    pi_event = event.get("event")
    if isinstance(pi_event, dict) and pi_event.get("type") == "turn_completed":
        return pi_event
    return None


def _raw_acp_stop_reason(event: dict[str, Any]) -> str | None:
    notification = event.get("notification")
    if event.get("type") != "notification" or not isinstance(notification, dict):
        return None
    result = notification.get("result")
    if not isinstance(result, dict):
        return None
    stop_reason = result.get("stopReason")
    return stop_reason if isinstance(stop_reason, str) else None


def is_turn_complete(event: dict[str, Any]) -> bool:
    """True for an ACP prompt result with `end_turn`, a `_posthog/turn_complete` notification, or a Pi `turn_completed` event."""
    if _pi_turn_completed(event) is not None:
        return True
    if _notification_method(event) == TURN_COMPLETE_METHOD:
        return True
    return _raw_acp_stop_reason(event) == STOP_REASON_END_TURN


def is_background_turn_complete(event: dict[str, Any]) -> bool:
    return _notification_method(event) == BACKGROUND_TURN_COMPLETE_METHOD


def pi_turn_error(event: dict[str, Any]) -> bool:
    """True when a Pi `turn_completed` event ended with a runtime error rather than a normal stop."""
    pi_event = _pi_turn_completed(event)
    return pi_event is not None and pi_event.get("stopReason") == "error"


def is_idle_resume_turn_complete(event: dict[str, Any]) -> bool:
    """An idle resume closes out the turn without the agent having answered a user prompt."""
    if _notification_method(event) != TURN_COMPLETE_METHOD:
        return False
    return _notification_params(event).get("stopReason") == STOP_REASON_IDLE_RESUME


def turn_completed_successfully(event: dict[str, Any]) -> bool:
    pi_event = _pi_turn_completed(event)
    if pi_event is not None:
        return pi_event.get("stopReason") == STOP_REASON_END_TURN
    if _notification_method(event) == TURN_COMPLETE_METHOD:
        return _notification_params(event).get("stopReason") == STOP_REASON_END_TURN
    return _raw_acp_stop_reason(event) == STOP_REASON_END_TURN


def turn_complete_trace_id(event: dict[str, Any]) -> str | None:
    trace_id = _notification_params(event).get("traceId")
    return trace_id if isinstance(trace_id, str) and trace_id else None
