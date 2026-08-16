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


# ---- Knowledge base schemas ----

class InstituteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    facilities: Optional[list[str]] = None
    extra_info: Optional[list[str]] = None


class CallingReasonUpdate(BaseModel):
    text: str


class TermsUpdate(BaseModel):
    terms: list[str]


class CourseCreate(BaseModel):
    key: str
    name: str
    price: str


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[str] = None