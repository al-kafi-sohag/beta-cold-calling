import time
import threading

_lock = threading.Lock()
_calls: dict[str, dict] = {}  # call_id (phone) -> record


def _get_or_create(call_id: str) -> dict:
    if call_id not in _calls:
        _calls[call_id] = {
            "call_id": call_id,
            "phone": call_id,
            "name": "",
            "course_key": "",
            "direction": "unknown",
            "twilio_sid": None,
            "twilio_status": None,
            "call_duration_sec": None,
            "started_at": time.time(),
            "ended_at": None,
            "final_status": None,
            "events": [],
        }
    return _calls[call_id]


def new_call(call_id: str, phone: str, name: str, course_key: str, direction: str = "outbound"):
    with _lock:
        record = _get_or_create(call_id)
        record.update({
            "phone": phone,
            "name": name,
            "course_key": course_key,
            "direction": direction,
            "started_at": time.time(),
            "ended_at": None,
            "final_status": None,
        })
    log_event(call_id, "call_created", f"Session created for {name} ({phone}), course={course_key}")
    return record


def set_twilio_sid(call_id: str, sid: str):
    with _lock:
        _get_or_create(call_id)["twilio_sid"] = sid
    log_event(call_id, "twilio_sid", f"Twilio call SID: {sid}")


def set_twilio_status(call_id: str, status: str, duration: str | None = None, extra: dict | None = None):
    with _lock:
        record = _get_or_create(call_id)
        record["twilio_status"] = status
        if duration is not None:
            record["call_duration_sec"] = duration
    log_event(call_id, "twilio_status", f"Twilio status callback: {status}"
               + (f" (duration={duration}s)" if duration else ""), extra=extra)


def log_event(call_id: str, event_type: str, message: str, level: str = "info", extra: dict | None = None):
    with _lock:
        record = _get_or_create(call_id)
        record["events"].append({
            "ts": time.time(),
            "type": event_type,
            "level": level,
            "message": message,
            "extra": extra or {},
        })


def end_call(call_id: str, final_status: str):
    with _lock:
        record = _get_or_create(call_id)
        record["ended_at"] = time.time()
        record["final_status"] = final_status
    log_event(call_id, "call_ended", f"Final status: {final_status}")


def get_call(call_id: str):
    with _lock:
        return _calls.get(call_id)


def list_calls():
    with _lock:
        return sorted(_calls.values(), key=lambda c: c["started_at"], reverse=True)