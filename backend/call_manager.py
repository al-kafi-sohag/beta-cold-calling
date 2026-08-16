import logging
from backend.knowledge_base import build_system_prompt
from backend.config import MAX_TURNS

logger = logging.getLogger("call_agent.session")

# In-memory session store: { phone: {history, turn_count, lead_name, course_key, transcript_lines} }
_sessions: dict[str, dict] = {}


def start_session(phone: str, lead_name: str, course_key: str):
    system_prompt = build_system_prompt(lead_name, course_key)
    _sessions[phone] = {
        "history": [{"role": "system", "content": system_prompt}],
        "turn_count": 0,
        "lead_name": lead_name,
        "course_key": course_key,
        "transcript_lines": [],
    }
    logger.info("Session started for %s (%s)", lead_name, phone)
    return _sessions[phone]


def get_session(phone: str):
    if phone not in _sessions:
        raise KeyError(f"No active session for {phone}. Call /api/call/start first.")
    return _sessions[phone]


def append_turn(phone: str, lead_text: str, agent_raw: str, agent_clean: str):
    session = get_session(phone)
    session["history"].append({"role": "user", "content": lead_text})
    session["history"].append({"role": "assistant", "content": agent_raw})
    session["transcript_lines"].append(f"LEAD: {lead_text}")
    session["transcript_lines"].append(f"AGENT: {agent_clean}")
    session["turn_count"] += 1


def append_opening(phone: str, agent_clean: str):
    session = get_session(phone)
    session["transcript_lines"].append(f"AGENT: {agent_clean}")


def is_call_over(phone: str, status: str) -> bool:
    """Call only ends when the lead clearly says yes/no.
    MAX_TURNS=0 (default) disables the turn-count cutoff entirely."""
    session = get_session(phone)
    if status in ("interested", "not_interested"):
        return True
    if MAX_TURNS and session["turn_count"] >= MAX_TURNS:
        return True
    return False


def end_session(phone: str):
    session = _sessions.pop(phone, None)
    return session