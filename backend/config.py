import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_free_groq_key_here")
LEADS_CSV_PATH = os.environ.get("LEADS_CSV_PATH", "leads.csv")
TRANSCRIPTS_DIR = os.environ.get("TRANSCRIPTS_DIR", "transcripts")
AUDIO_TMP_DIR = os.environ.get("AUDIO_TMP_DIR", "tmp_audio")
STT_LANGUAGE = "bn-BD"
TTS_LANGUAGE = "bn"
LLM_MODEL = "llama-3.3-70b-versatile"
MAX_TURNS = 8

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")
TWILIO_GATHER_LANGUAGE = os.environ.get("TWILIO_GATHER_LANGUAGE", "bn-IN")

os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(AUDIO_TMP_DIR, exist_ok=True)