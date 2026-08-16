import pandas as pd
import os
import datetime
from backend.config import LEADS_CSV_PATH, TRANSCRIPTS_DIR

REQUIRED_COLUMNS = ["phone", "name", "course_key", "status", "notes", "transcript_file"]


def ensure_leads_csv():
    if not os.path.exists(LEADS_CSV_PATH):
        df = pd.DataFrame({
            "phone": ["+8801773301138", "+8801773301138"],
            "name": ["Rahim", "Karim"],
            "course_key": ["digital_marketing", "web_design"],
            "status": ["not_called", "not_called"],
            "notes": ["", ""],
            "transcript_file": ["", ""],
        })
        df.to_csv(LEADS_CSV_PATH, index=False)


def read_leads():
    ensure_leads_csv()
    df = pd.read_csv(LEADS_CSV_PATH, dtype=str)
    df = df.fillna("")
    return df


def update_lead_status(phone: str, status: str, transcript_path: str, note: str = ""):
    df = read_leads()
    mask = df["phone"] == phone
    if not mask.any():
        raise ValueError(f"Lead with phone {phone} not found")
    df.loc[mask, "status"] = status
    df.loc[mask, "transcript_file"] = transcript_path
    df.loc[mask, "notes"] = note or f"Called at {datetime.datetime.now().isoformat()}"
    df.to_csv(LEADS_CSV_PATH, index=False)


def save_transcript(phone: str, lines: list[str]) -> str:
    safe_phone = phone.replace("+", "").replace(" ", "")
    path = os.path.join(TRANSCRIPTS_DIR, f"{safe_phone}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def add_lead(phone: str, name: str, course_key: str):
    df = read_leads()
    if (df["phone"] == phone).any():
        raise ValueError(f"Lead with phone {phone} already exists")
    new_row = {
        "phone": phone,
        "name": name,
        "course_key": course_key,
        "status": "not_called",
        "notes": "",
        "transcript_file": "",
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(LEADS_CSV_PATH, index=False)
    return new_row


def delete_lead(phone: str):
    df = read_leads()
    mask = df["phone"] == phone
    if not mask.any():
        raise ValueError(f"Lead with phone {phone} not found")
    df = df[~mask]
    df.to_csv(LEADS_CSV_PATH, index=False)


def reset_lead(phone: str):
    """Reset a lead back to not_called so it can be dialed again."""
    df = read_leads()
    mask = df["phone"] == phone
    if not mask.any():
        raise ValueError(f"Lead with phone {phone} not found")
    df.loc[mask, "status"] = "not_called"
    df.loc[mask, "notes"] = ""
    df.loc[mask, "transcript_file"] = ""
    df.to_csv(LEADS_CSV_PATH, index=False)