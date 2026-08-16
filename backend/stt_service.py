import time
import logging
import httpx
import speech_recognition as sr
from pydub import AudioSegment
from backend.config import STT_LANGUAGE, AUDIO_TMP_DIR, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
import os
import uuid

logger = logging.getLogger("call_agent.stt")
recognizer = sr.Recognizer()


def transcribe_audio_file(upload_path: str) -> dict:
    wav_path = os.path.join(AUDIO_TMP_DIR, f"conv_{uuid.uuid4().hex}.wav")

    t0 = time.time()
    audio = AudioSegment.from_file(upload_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")
    convert_elapsed = round(time.time() - t0, 2)

    duration_sec = round(len(audio) / 1000.0, 2)
    volume_dbfs = audio.dBFS
    logger.info(
        "Converted upload in %.2fs — duration=%.2fs avg_volume=%.1fdBFS",
        convert_elapsed, duration_sec, volume_dbfs if volume_dbfs != float("-inf") else -99,
    )

    text = ""
    error = None
    t1 = time.time()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=STT_LANGUAGE)
    except sr.UnknownValueError:
        error = "STT could not understand the audio (silence or unclear speech)"
        logger.warning(error)
    except sr.RequestError as e:
        error = f"STT request failed: {e}"
        logger.error(error)
    stt_elapsed = round(time.time() - t1, 2)

    logger.info("STT done in %.2fs — heard: \"%s\"", stt_elapsed, text)

    return {
        "text": text,
        "error": error,
        "duration_sec": duration_sec,
        "volume_dbfs": volume_dbfs if volume_dbfs != float("-inf") else -99,
        "convert_time_sec": convert_elapsed,
        "stt_time_sec": stt_elapsed,
        "wav_path": wav_path,
    }


def download_and_transcribe_recording(recording_url: str) -> dict:
    """Download a Twilio call recording (given the RecordingUrl from a <Record> callback)
    and transcribe it using the same Google STT pipeline as the browser flow."""
    wav_url = f"{recording_url}.wav"
    upload_path = os.path.join(AUDIO_TMP_DIR, f"twilio_rec_{uuid.uuid4().hex}.wav")

    logger.info("Downloading Twilio recording from %s", wav_url)

    resp = None
    last_error = None
    with httpx.Client(timeout=20.0) as client:
        for attempt in range(3):
            try:
                resp = client.get(wav_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
                resp.raise_for_status()
                break
            except Exception as e:
                last_error = e
                logger.warning("Recording download attempt %d failed: %s", attempt + 1, e)
                time.sleep(1)

    if resp is None:
        raise RuntimeError(f"Failed to download Twilio recording after retries: {last_error}")

    with open(upload_path, "wb") as f:
        f.write(resp.content)

    logger.info("Downloaded recording to %s (%d bytes)", upload_path, len(resp.content))

    return transcribe_audio_file(upload_path)