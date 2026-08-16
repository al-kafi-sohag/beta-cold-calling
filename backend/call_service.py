import logging
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

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
        raise RuntimeError("PUBLIC_BASE_URL not set")
    return f"{PUBLIC_BASE_URL}/audio/{filename}"


def twiml_url(path: str) -> str:
    if not PUBLIC_BASE_URL:
        raise RuntimeError("PUBLIC_BASE_URL not set")
    return f"{PUBLIC_BASE_URL}{path}"


def place_call(to_number: str, phone_id: str) -> str:
    """Dial the lead. phone_id is used to build the webhook URL Twilio calls first."""
    client = get_twilio_client()
    if not TWILIO_FROM_NUMBER:
        raise RuntimeError("TWILIO_FROM_NUMBER not set")

    call = client.calls.create(
        to=to_number,
        from_=TWILIO_FROM_NUMBER,
        url=twiml_url(f"/twiml/opening?phone={phone_id}"),
        method="POST",
        status_callback=twiml_url(f"/twilio/status?phone={phone_id}"),
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        status_callback_method="POST",
    )
    logger.info("Placed Twilio call sid=%s to=%s", call.sid, to_number)
    call_logs.set_twilio_sid(phone_id, call.sid)
    return call.sid


def build_gather_response(audio_filename: str, action_path: str, phone_id: str) -> str:
    vr = VoiceResponse()
    vr.play(audio_url(audio_filename))
    gather = Gather(
        input="speech",
        action=twiml_url(f"{action_path}?phone={phone_id}"),
        method="POST",
        language=TWILIO_GATHER_LANGUAGE,
        speech_timeout="auto",
    )
    vr.append(gather)
    vr.redirect(twiml_url(f"{action_path}?phone={phone_id}&empty=1"), method="POST")
    return str(vr)


def build_final_response(audio_filename: str) -> str:
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