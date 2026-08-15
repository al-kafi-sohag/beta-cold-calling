from pydantic import BaseModel
from typing import Optional


class StartCallResponse(BaseModel):
    call_id: str
    agent_text: str
    agent_audio_base64: str
    status: str


class TurnResponse(BaseModel):
    call_id: str
    lead_text: str
    agent_text: str
    agent_audio_base64: str
    status: str
    call_ended: bool
    timings: dict


class LeadOut(BaseModel):
    phone: str
    name: str
    course_key: str
    status: str
    notes: Optional[str] = ""
    transcript_file: Optional[str] = ""