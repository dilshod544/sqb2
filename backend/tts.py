import asyncio
import io
import os
import re

from backend.uz_text import clean_for_speech

VOICE = os.getenv("TTS_VOICE", "uz-UZ-MadinaNeural")
TTS_RATE = os.getenv("TTS_RATE", "+8%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")


async def _edge_tts(text: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()


def _prepare_text(text: str) -> str:
    text = clean_for_speech(text)
    # O'zbek apostroflari — TTS uchun yaxshiroq
    text = text.replace("ʻ", "'").replace("'", "'")
    text = re.sub(r"[^\w\s\d.,!?'+\-]", "", text, flags=re.UNICODE)
    return text.strip()


def text_to_speech(text: str) -> bytes | None:
    prepared = _prepare_text(text)
    if not prepared or len(prepared) < 2:
        return None
    try:
        return asyncio.run(_edge_tts(prepared))
    except Exception as e:
        print(f"Edge TTS xato ({e})")
        return None
