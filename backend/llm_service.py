import re
import time
import logging
from groq import Groq
from backend.config import GROQ_API_KEY, LLM_MODEL

logger = logging.getLogger("call_agent.llm")
client = Groq(api_key=GROQ_API_KEY)

STATUS_PATTERN = re.compile(
    r"STATUS:\s*(interested|not_interested|callback_requested|undecided)",
    re.IGNORECASE,
)


def parse_status_and_clean(reply_text: str):
    match = STATUS_PATTERN.search(reply_text)
    status = match.group(1).lower() if match else "undecided"
    clean_text = STATUS_PATTERN.sub("", reply_text).strip()
    return clean_text, status


def get_agent_reply(conversation_history: list[dict]):
    logger.info("Sending conversation to LLM (Groq, %s)...", LLM_MODEL)
    t0 = time.time()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=conversation_history,
        temperature=0.4,
    )
    raw_reply = response.choices[0].message.content
    elapsed = round(time.time() - t0, 2)
    clean_reply, status = parse_status_and_clean(raw_reply)
    logger.info("LLM responded in %.2fs — status=%s — reply=\"%s\"", elapsed, status, clean_reply)
    return raw_reply, clean_reply, status, elapsed