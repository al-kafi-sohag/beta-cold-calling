import logging
from backend.knowledge_base import build_system_prompt, COURSES
from backend.config import MAX_TURNS

logger = logging.getLogger("call_agent.session")

# In-memory session store: { phone: {history, turn_count, lead_name, course_key, stt_mode, transcript_lines} }
_sessions: dict[str, dict] = {}


def start_session(phone: str, lead_name: str, course_key: str, stt_mode: str = "record"):
    system_prompt = build_system_prompt(lead_name, course_key)
    _sessions[phone] = {
        "history": [{"role": "system", "content": system_prompt}],
        "turn_count": 0,
        "lead_name": lead_name,
        "course_key": course_key,
        "stt_mode": stt_mode,  # "record" (download+transcribe) or "gather" (Twilio built-in)
        "transcript_lines": [],
    }
    logger.info("Session started for %s (%s) — stt_mode=%s", lead_name, phone, stt_mode)
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
    session = get_session(phone)
    if status in ("interested", "not_interested"):
        return True
    # MAX_TURNS == 0 means "infinite" — never auto-end on turn count.
    if MAX_TURNS and session["turn_count"] >= MAX_TURNS:
        return True
    return False


def end_session(phone: str):
    session = _sessions.pop(phone, None)
    return session
python
# backend/call_service.py
import logging
from urllib.parse import quote
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Record, Gather

from backend.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    PUBLIC_BASE_URL,
    TWILIO_GATHER_LANGUAGE,
)
from backend import call_logs

logger = logging.getLogger("call_agent.telephony")

_client = None


def get_twilio_client() -> Client:
    global _client
    if _client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise RuntimeError("TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set")
        _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _client


def audio_url(filename: str) -> str:
    if not PUBLIC_BASE_URL:
        raise RuntimeError("PUBLIC_BASE_URL not set — start ngrok and set it")
    return f"{PUBLIC_BASE_URL}/audio/{filename}"


def twiml_url(path: str) -> str:
    if not PUBLIC_BASE_URL:
        raise RuntimeError("PUBLIC_BASE_URL not set — start ngrok and set it")
    return f"{PUBLIC_BASE_URL}{path}"


def _enc(phone: str) -> str:
    """Percent-encode phone numbers before embedding in a query string.
    A raw '+' in a query string decodes as a space, breaking session lookups."""
    return quote(phone, safe="")


def place_call(to_number: str, phone_id: str) -> str:
    """Dial the lead. phone_id is used to build the webhook URL Twilio calls first."""
    client = get_twilio_client()
    if not TWILIO_FROM_NUMBER:
        raise RuntimeError("TWILIO_FROM_NUMBER not set")

    encoded_phone = _enc(phone_id)
    call = client.calls.create(
        to=to_number,
        from_=TWILIO_FROM_NUMBER,
        url=twiml_url(f"/twiml/opening?phone={encoded_phone}"),
        method="POST",
        status_callback=twiml_url(f"/twilio/status?phone={encoded_phone}"),
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        status_callback_method="POST",
    )
    logger.info("Placed Twilio call sid=%s to=%s", call.sid, to_number)
    call_logs.set_twilio_sid(phone_id, call.sid)
    return call.sid


def build_record_response(audio_filename: str, action_path: str, phone_id: str) -> str:
    """Play the agent's line, then RECORD the lead's reply (downloaded + transcribed
    via our own Bengali STT pipeline, same as the browser flow). More accurate for
    Bengali, but adds a download+convert round trip before each reply."""
    encoded_phone = _enc(phone_id)
    vr = VoiceResponse()
    vr.play(audio_url(audio_filename))
    record = Record(
        action=twiml_url(f"{action_path}?phone={encoded_phone}"),
        method="POST",
        max_length=30,
        timeout=2,
        play_beep=True,
        trim="trim-silence",
        finish_on_key="",
    )
    vr.append(record)
    # If Record gets zero input at all, Twilio falls through to here
    vr.redirect(twiml_url(f"{action_path}?phone={encoded_phone}&empty=1"), method="POST")
    return str(vr)


def build_gather_response(audio_filename: str, action_path: str, phone_id: str) -> str:
    """Play the agent's line, then use Twilio's built-in speech recognition (Gather).
    Faster — no download/transcribe round trip, SpeechResult comes back immediately —
    but Bengali recognition accuracy is generally weaker than the Record+STT pipeline."""
    encoded_phone = _enc(phone_id)
    vr = VoiceResponse()
    vr.play(audio_url(audio_filename))
    gather = Gather(
        input="speech",
        action=twiml_url(f"{action_path}?phone={encoded_phone}"),
        method="POST",
        language=TWILIO_GATHER_LANGUAGE,
        speech_timeout="auto",
    )
    vr.append(gather)
    # If Gather gets zero input at all, Twilio falls through to here
    vr.redirect(twiml_url(f"{action_path}?phone={encoded_phone}&empty=1"), method="POST")
    return str(vr)


def build_final_response(audio_filename: str) -> str:
    """Play the closing line, then hang up."""
    vr = VoiceResponse()
    vr.play(audio_url(audio_filename))
    vr.hangup()
    return str(vr)


def build_say_fallback(message: str, language: str = "bn-IN") -> str:
    """Ultimate fallback that doesn't depend on our TTS/network at all — uses Twilio's own voice."""
    vr = VoiceResponse()
    vr.say(message, language=language)
    vr.hangup()
    return str(vr)