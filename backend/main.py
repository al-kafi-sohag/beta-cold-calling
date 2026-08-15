import logging
import os
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import AUDIO_TMP_DIR
from backend.knowledge_base import COURSES
from backend.schemas import StartCallResponse, TurnResponse, LeadOut
from backend import csv_service, call_manager
from backend.llm_service import get_agent_reply
from backend.tts_service import synthesize_speech
from backend.stt_service import transcribe_audio_file
from fastapi.responses import Response
from backend import call_service

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


@app.get("/api/leads", response_model=list[LeadOut])
def list_leads():
    df = csv_service.read_leads()
    return df.fillna("").to_dict(orient="records")


@app.get("/api/courses")
def list_courses():
    return COURSES


@app.post("/api/call/start", response_model=StartCallResponse)
def start_call(phone: str = Form(...), name: str = Form(...), course_key: str = Form(...)):
    if course_key not in COURSES:
        raise HTTPException(400, f"Unknown course_key: {course_key}")

    logger.info("CALL START — %s (%s) course=%s", name, phone, course_key)
    call_manager.start_session(phone, name, course_key)
    session = call_manager.get_session(phone)

    opener_prompt = session["history"] + [{"role": "user", "content": "কল শুরু কর।"}]
    raw_reply, clean_reply, status, _ = get_agent_reply(opener_prompt)
    session["history"].append({"role": "assistant", "content": raw_reply})
    call_manager.append_opening(phone, clean_reply)

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
        logger.warning("Empty transcription for %s — asking lead to repeat", phone)
        repeat_text = "দুঃখিত, ঠিক শুনতে পাইনি। আবার একটু বলবেন কি?\nSTATUS: undecided"
        clean_reply, status = repeat_text.split("\nSTATUS:")[0].strip(), "undecided"
        tts_result = synthesize_speech(clean_reply)
        return TurnResponse(
            call_id=phone,
            lead_text="",
            agent_text=clean_reply,
            agent_audio_base64=tts_result["audio_base64"],
            status=status,
            call_ended=False,
            timings=timings,
        )

    raw_reply, clean_reply, status, llm_time = get_agent_reply(
        session["history"] + [{"role": "user", "content": lead_text}]
    )
    call_manager.append_turn(phone, lead_text, raw_reply, clean_reply)
    timings["llm_time_sec"] = llm_time

    tts_result = synthesize_speech(clean_reply)
    timings["tts_time_sec"] = tts_result["gen_time_sec"]
    timings["tts_duration_sec"] = tts_result["duration_sec"]

    call_ended = call_manager.is_call_over(phone, status)

    if call_ended:
        session_data = call_manager.end_session(phone)
        transcript_path = csv_service.save_transcript(phone, session_data["transcript_lines"])
        csv_service.update_lead_status(phone, status, transcript_path)
        logger.info("CALL END — %s — final status=%s — transcript=%s", phone, status, transcript_path)

    return TurnResponse(
        call_id=phone,
        lead_text=lead_text,
        agent_text=clean_reply,
        agent_audio_base64=tts_result["audio_base64"],
        status=status,
        call_ended=call_ended,
        timings=timings,
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


@app.post("/api/call/dial")
def dial_call(phone: str = Form(...), name: str = Form(...), course_key: str = Form(...)):
    if course_key not in COURSES:
        raise HTTPException(400, f"Unknown course_key: {course_key}")

    logger.info("DIAL — %s (%s) course=%s", name, phone, course_key)
    call_manager.start_session(phone, name, course_key)

    call_sid = call_service.place_call(phone, phone_id=phone)
    return {"phone": phone, "call_sid": call_sid, "status": "dialing"}


@app.post("/twiml/opening")
def twiml_opening(phone: str):
    try:
        session = call_manager.get_session(phone)
    except KeyError:
        logger.warning("twiml_opening called with no session for %s", phone)
        vr_error = call_service.build_final_response(
            os.path.basename(synthesize_speech("দুঃখিত, একটি সমস্যা হয়েছে। আবার চেষ্টা করুন।")["file_path"])
        )
        return Response(content=vr_error, media_type="application/xml")

    opener_prompt = session["history"] + [{"role": "user", "content": "কল শুরু কর।"}]
    raw_reply, clean_reply, status, _ = get_agent_reply(opener_prompt)
    session["history"].append({"role": "assistant", "content": raw_reply})
    call_manager.append_opening(phone, clean_reply)

    tts_result = synthesize_speech(clean_reply)
    audio_filename = os.path.basename(tts_result["file_path"])

    twiml = call_service.build_gather_response(audio_filename, "/twiml/turn", phone)
    return Response(content=twiml, media_type="application/xml")

@app.post("/twiml/turn")
def twiml_turn(phone: str, SpeechResult: str = Form(default=""), empty: str = "0"):
    try:
        session = call_manager.get_session(phone)
    except KeyError:
        vr_error = call_service.build_final_response(
            os.path.basename(synthesize_speech("দুঃখিত, একটি সমস্যা হয়েছে।")["file_path"])
        )
        return Response(content=vr_error, media_type="application/xml")

    lead_text = SpeechResult.strip()

    if not lead_text:
        logger.warning("No speech captured for %s — asking to repeat", phone)
        repeat_text = "দুঃখিত, ঠিক শুনতে পাইনি। আবার একটু বলবেন কি?"
        tts_result = synthesize_speech(repeat_text)
        audio_filename = os.path.basename(tts_result["file_path"])
        twiml = call_service.build_gather_response(audio_filename, "/twiml/turn", phone)
        return Response(content=twiml, media_type="application/xml")

    raw_reply, clean_reply, status, llm_time = get_agent_reply(
        session["history"] + [{"role": "user", "content": lead_text}]
    )
    call_manager.append_turn(phone, lead_text, raw_reply, clean_reply)

    tts_result = synthesize_speech(clean_reply)
    audio_filename = os.path.basename(tts_result["file_path"])

    call_ended = call_manager.is_call_over(phone, status)

    if call_ended:
        session_data = call_manager.end_session(phone)
        transcript_path = csv_service.save_transcript(phone, session_data["transcript_lines"])
        csv_service.update_lead_status(phone, status, transcript_path)
        logger.info("CALL END — %s — final status=%s — transcript=%s", phone, status, transcript_path)
        twiml = call_service.build_final_response(audio_filename)
    else:
        twiml = call_service.build_gather_response(audio_filename, "/twiml/turn", phone)

    return Response(content=twiml, media_type="application/xml")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")