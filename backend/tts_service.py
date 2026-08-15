import time
import base64
import logging
from gtts import gTTS
from pydub import AudioSegment
from backend.config import TTS_LANGUAGE, AUDIO_TMP_DIR
import os
import uuid

logger = logging.getLogger("call_agent.tts")


def synthesize_speech(text: str) -> dict:
    logger.info("Generating TTS for text length=%d chars", len(text))
    t0 = time.time()
    filename = os.path.join(AUDIO_TMP_DIR, f"reply_{uuid.uuid4().hex}.mp3")
    tts = gTTS(text=text, lang=TTS_LANGUAGE)
    tts.save(filename)
    elapsed = round(time.time() - t0, 2)

    duration_sec = round(len(AudioSegment.from_file(filename)) / 1000.0, 2)

    with open(filename, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    logger.info("TTS generated in %.2fs — audio length=%.2fs", elapsed, duration_sec)
    return {
        "audio_base64": audio_b64,
        "duration_sec": duration_sec,
        "gen_time_sec": elapsed,
        "file_path": filename,
    }