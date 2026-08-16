import logging
import os
import shutil
import time
import traceback
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse

from backend.config import AUDIO_TMP_DIR
from backend.knowledge_base import COURSES
from backend.schemas import StartCallResponse, TurnResponse, LeadOut
from backend import csv_service, call_manager, call_logs, call_service
from backend.llm_service import get_agent_reply
from backend.tts_service import synthesize_speech
from backend.stt_service import transcribe_audio_file

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("call_agent.api")

app = FastAPI(title="Bengali Cold-Call Agent Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

csv_service.ensure_leads_csv()

FALLBACK_MESSAGE = "দুঃখিত, একটি প্রযুক্তিগত সমস্যা হয়েছে। আমরা পরে আবার যোগাযোগ করব। ধন্যবাদ।"


def _error_twiml(phone: str, reason: str) -> str:
    """Always returns valid TwiML, even if our own TTS/network is down."""
    call_logs.log_event(phone, "fallback_twiml", f"Returning fallback TwiML: {reason}", level="error")
    try:
        tts_result = synthesize_speech(FALLBACK_MESSAGE)
        return call_service.build_final_response(os.path.basename(tts_result["file_path"]))
    except Exception as e:
        logger.exception("Even fallback TTS failed for %s", phone)
        call_logs.log_event(phone, "fallback_tts_failed", f"{type(e).__name__}: {e}", level="error")
        # Twilio's own <Say> voice — does not depend on our server/network at all
        return call_service.build_say_fallback(FALLBACK_MESSAGE)


@app.get("/api/leads", response_model=list[LeadOut])
def list_leads():
    df = csv_service.read_leads()
    return df.fillna("").to_dict(orient="records")


@app.post("/api/leads")
def create_lead(phone: str = Form(...), name: str = Form(...), course_key: str = Form(...)):
    if course_key not in COURSES:
        raise HTTPException(400, f"Unknown course_key: {course_key}")
    lead = csv_service.add_lead(phone, name, course_key)
    logger.info("Added new lead: %s (%s)", name, phone)
    return lead


@app.get("/api/courses")
def list_courses():
    return COURSES


# ---------- Web-test endpoints (browser mic, no Twilio) ----------

@app.post("/api/call/start", response_model=StartCallResponse)
def start_call(phone: str = Form(...), name: str = Form(...), course_key: str = Form(...)):
    if course_key not in COURSES:
        raise HTTPException(400, f"Unknown course_key: {course_key}")

    logger.info("CALL START (web) — %s (%s) course=%s", name, phone, course_key)
    call_logs.new_call(phone, phone, name, course_key, direction="web_test")
    call_manager.start_session(phone, name, course_key)
    session = call_manager.get_session(phone)

    opener_prompt = session["history"] + [{"role": "user", "content": "কল শুরু কর।"}]
    raw_reply, clean_reply, status, _ = get_agent_reply(opener_prompt)
    session["history"].append({"role": "assistant", "content": raw_reply})
    call_manager.append_opening(phone, clean_reply)
    call_logs.log_event(phone, "agent_opening", clean_reply, extra={"status": status})

    tts_result = synthesize_speech(clean_reply)

    return StartCallResponse(
        call_id=phone,
        agent_text=clean_reply,
        agent_audio_base64=tts_result["audio_base64"],
        status=status,
    )


@app.post("/api/call/turn", response_model=TurnResponse)
async def call_turn(phone: str = Form(...), audio: UploadFile = File(...)):
    try:
        session = call_manager.get_session(phone)
    except KeyError as e:
        raise HTTPException(400, str(e))

    upload_path = os.path.join(AUDIO_TMP_DIR, f"upload_{uuid.uuid4().hex}.webm")
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    stt_result = transcribe_audio_file(upload_path)
    lead_text = stt_result["text"]

    timings = {
        "stt_convert_sec": stt_result["convert_time_sec"],
        "stt_time_sec": stt_result["stt_time_sec"],
        "volume_dbfs": stt_result["volume_dbfs"],
    }

    if not lead_text.strip():
        call_logs.log_event(phone, "stt_empty", "No speech transcribed", level="warn")
        repeat_text = "দুঃখিত, ঠিক শুনতে পাইনি। আবার একটু বলবেন কি?"
        tts_result = synthesize_speech(repeat_text)
        return TurnResponse(
            call_id=phone, lead_text="", agent_text=repeat_text,
            agent_audio_base64=tts_result["audio_base64"], status="undecided",
            call_ended=False, timings=timings,
        )

    call_logs.log_event(phone, "stt_result", lead_text)
    raw_reply, clean_reply, status, llm_time = get_agent_reply(
        session["history"] + [{"role": "user", "content": lead_text}]
    )
    call_manager.append_turn(phone, lead_text, raw_reply, clean_reply)
    call_logs.log_event(phone, "agent_reply", clean_reply, extra={"status": status})
    timings["llm_time_sec"] = llm_time

    tts_result = synthesize_speech(clean_reply)
    timings["tts_time_sec"] = tts_result["gen_time_sec"]
    timings["tts_duration_sec"] = tts_result["duration_sec"]

    call_ended = call_manager.is_call_over(phone, status)
    if call_ended:
        session_data = call_manager.end_session(phone)
        transcript_path = csv_service.save_transcript(phone, session_data["transcript_lines"])
        csv_service.update_lead_status(phone, status, transcript_path)
        call_logs.end_call(phone, status)

    return TurnResponse(
        call_id=phone, lead_text=lead_text, agent_text=clean_reply,
        agent_audio_base64=tts_result["audio_base64"], status=status,
        call_ended=call_ended, timings=timings,
    )


@app.get("/api/transcript/{phone}")
def get_transcript(phone: str):
    df = csv_service.read_leads()
    row = df[df["phone"] == phone]
    if row.empty or not row.iloc[0]["transcript_file"]:
        raise HTTPException(404, "Transcript not found")
    path = row.iloc[0]["transcript_file"]
    if not os.path.exists(path):
        raise HTTPException(404, "Transcript file missing on disk")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"phone": phone, "transcript": content}


app.mount("/audio", StaticFiles(directory=AUDIO_TMP_DIR), name="audio")


# ---------- Real Twilio phone calls ----------

@app.post("/api/call/dial")
def dial_call(phone: str = Form(...), name: str = Form(...), course_key: str = Form(...)):
    if course_key not in COURSES:
        raise HTTPException(400, f"Unknown course_key: {course_key}")

    logger.info("DIAL — %s (%s) course=%s", name, phone, course_key)
    call_logs.new_call(phone, phone, name, course_key, direction="twilio_outbound")
    call_manager.start_session(phone, name, course_key)

    try:
        call_sid = call_service.place_call(phone, phone_id=phone)
    except Exception as e:
        logger.exception("place_call failed for %s", phone)
        call_logs.log_event(phone, "dial_error", f"{type(e).__name__}: {e}", level="error")
        raise HTTPException(500, f"Failed to place call: {e}")

    return {"phone": phone, "call_sid": call_sid, "status": "dialing"}


@app.post("/twiml/opening")
def twiml_opening(phone: str):
    call_logs.log_event(phone, "webhook_hit", "Twilio hit /twiml/opening")
    try:
        session = call_manager.get_session(phone)
    except KeyError:
        return Response(content=_error_twiml(phone, "no active session"), media_type="application/xml")

    try:
        opener_prompt = session["history"] + [{"role": "user", "content": "কল শুরু কর।"}]
        t0 = time.time()
        raw_reply, clean_reply, status, _ = get_agent_reply(opener_prompt)
        call_logs.log_event(phone, "llm_reply",
                             f"Opener LLM reply in {round(time.time() - t0, 2)}s: {clean_reply}",
                             extra={"status": status})
        session["history"].append({"role": "assistant", "content": raw_reply})
        call_manager.append_opening(phone, clean_reply)

        t1 = time.time()
        tts_result = synthesize_speech(clean_reply)
        call_logs.log_event(phone, "tts_done", f"TTS generated in {round(time.time() - t1, 2)}s")
        audio_filename = os.path.basename(tts_result["file_path"])

        twiml = call_service.build_gather_response(audio_filename, "/twiml/turn", phone)
        call_logs.log_event(phone, "twiml_sent", "Sent opening Gather TwiML")
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.exception("Error in /twiml/opening for %s", phone)
        call_logs.log_event(phone, "exception", f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}",
                             level="error")
        return Response(content=_error_twiml(phone, str(e)), media_type="application/xml")


@app.post("/twiml/turn")
def twiml_turn(phone: str, SpeechResult: str = Form(default=""), empty: str = "0"):
    call_logs.log_event(phone, "webhook_hit", f"Twilio hit /twiml/turn (empty={empty})")
    try:
        session = call_manager.get_session(phone)
    except KeyError:
        return Response(content=_error_twiml(phone, "no active session"), media_type="application/xml")

    lead_text = SpeechResult.strip()

    try:
        if not lead_text:
            call_logs.log_event(phone, "stt_empty", "No SpeechResult from Twilio", level="warn")
            repeat_text = "দুঃখিত, ঠিক শুনতে পাইনি। আবার একটু বলবেন কি?"
            tts_result = synthesize_speech(repeat_text)
            audio_filename = os.path.basename(tts_result["file_path"])
            twiml = call_service.build_gather_response(audio_filename, "/twiml/turn", phone)
            return Response(content=twiml, media_type="application/xml")

        call_logs.log_event(phone, "stt_result", lead_text)
        t0 = time.time()
        raw_reply, clean_reply, status, llm_time = get_agent_reply(
            session["history"] + [{"role": "user", "content": lead_text}]
        )
        call_logs.log_event(phone, "llm_reply", f"{clean_reply} ({round(time.time() - t0, 2)}s)",
                             extra={"status": status})
        call_manager.append_turn(phone, lead_text, raw_reply, clean_reply)

        tts_result = synthesize_speech(clean_reply)
        audio_filename = os.path.basename(tts_result["file_path"])
        call_logs.log_event(phone, "tts_done", f"TTS generated in {tts_result['gen_time_sec']}s")

        call_ended = call_manager.is_call_over(phone, status)

        if call_ended:
            session_data = call_manager.end_session(phone)
            transcript_path = csv_service.save_transcript(phone, session_data["transcript_lines"])
            csv_service.update_lead_status(phone, status, transcript_path)
            call_logs.end_call(phone, status)
            twiml = call_service.build_final_response(audio_filename)
        else:
            twiml = call_service.build_gather_response(audio_filename, "/twiml/turn", phone)

        call_logs.log_event(phone, "twiml_sent", f"Sent turn TwiML (call_ended={call_ended})")
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        logger.exception("Error in /twiml/turn for %s", phone)
        call_logs.log_event(phone, "exception", f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}",
                             level="error")
        return Response(content=_error_twiml(phone, str(e)), media_type="application/xml")


@app.post("/twilio/status")
def twilio_status(phone: str, CallStatus: str = Form(default=""), CallDuration: str = Form(default=""),
                   CallSid: str = Form(default="")):
    """Twilio hits this on initiated/ringing/answered/completed — tells you the REAL reason a call ended."""
    call_logs.set_twilio_status(phone, CallStatus, duration=CallDuration or None,
                                 extra={"call_sid": CallSid})
    return Response(content="", media_type="text/plain")


# ---------- Monitoring API ----------

@app.get("/api/monitor/calls")
def monitor_list_calls():
    return call_logs.list_calls()


@app.get("/api/monitor/calls/{call_id}")
def monitor_call_detail(call_id: str):
    record = call_logs.get_call(call_id)
    if not record:
        raise HTTPException(404, "No such call")
    return record


@app.get("/dashboard")
def dashboard():
    return FileResponse("frontend/dashboard.html")


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")