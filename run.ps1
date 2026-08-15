python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

$env:GROQ_API_KEY = "REMOVED"

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000