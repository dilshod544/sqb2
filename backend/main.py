from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.stt import transcribe_audio
from backend.llm import get_customer_reply, get_evaluation, check_ollama_model, MODEL_NAME
from backend.tts import text_to_speech
from backend.scenarios import SCENARIOS
from backend.emotion import extract_emotion, apply_emotion_to_audio, opening_emotion_tag
from backend.uz_text import is_garbage
import json
import base64
import asyncio
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_tts_pool = ThreadPoolExecutor(max_workers=2)


@app.get("/scenarios")
async def get_scenarios():
    return SCENARIOS


@app.get("/health")
async def health():
    return {"status": "ok", "ollama": check_ollama_model()}


def _tts_with_emotion(sentence: str):
    emotion, clean = extract_emotion(sentence)
    clean = clean.replace("[SUHBAT_TUGADI]", "").strip()
    if not clean or is_garbage(clean):
        return None, emotion, sentence
    audio = text_to_speech(clean)
    if not audio:
        return None, emotion, sentence
    return base64.b64encode(apply_emotion_to_audio(audio, emotion)).decode(), emotion, sentence


@app.post("/process-stream")
async def process_voice_stream(
    audio: UploadFile = File(...),
    scenario_id: str = Form(...),
    history: str = Form(...),
):
    audio_bytes = await audio.read()
    user_text = transcribe_audio(audio_bytes)

    async def generate():
        if not user_text.strip():
            yield json.dumps({
                "type": "error",
                "text": "Tushunmadim. O'zbekcha, aniq gapiring.",
            }) + "\n"
            yield json.dumps({"type": "done", "is_final": False}) + "\n"
            return

        yield json.dumps({"type": "stt", "text": user_text}) + "\n"

        chat_history = json.loads(history)
        chat_history.append({"role": "user", "content": user_text})

        sentence_queue = queue.Queue()
        is_done_flag = [False]
        evaluation_text = ""

        def _user_wants_end(text: str) -> bool:
            t = text.lower()
            return any(w in t for w in ("xayr", "hayr", "salomat", "sog bo"))

        def run_pipeline():
            nonlocal evaluation_text
            try:
                reply = get_customer_reply(chat_history, scenario_id)
                audio_b64, emotion, sent = _tts_with_emotion(reply)
                sentence_queue.put({
                    "type": "llm_chunk",
                    "text": sent,
                    "emotion": emotion,
                    "audio_base64": audio_b64,
                    "is_evaluation": False,
                })

                user_turns = sum(1 for m in chat_history if m.get("role") == "user")
                if _user_wants_end(user_text) or user_turns >= 6:
                    evaluation_text = get_evaluation(chat_history, scenario_id)
                    sentence_queue.put({
                        "type": "llm_chunk",
                        "text": evaluation_text,
                        "emotion": None,
                        "audio_base64": None,
                        "is_evaluation": True,
                    })
            except Exception as e:
                print(f"Pipeline xato: {e}")
                sentence_queue.put({
                    "type": "error",
                    "text": "Xatolik. Qayta urinib ko'ring.",
                })
            finally:
                is_done_flag[0] = True

        threading.Thread(target=run_pipeline, daemon=True).start()

        while not is_done_flag[0] or not sentence_queue.empty():
            try:
                item = sentence_queue.get(timeout=0.1)
                yield json.dumps(item) + "\n"
            except queue.Empty:
                await asyncio.sleep(0.02)

        is_final = bool(evaluation_text) or _user_wants_end(user_text)
        yield json.dumps({
            "type": "done",
            "is_final": is_final,
            "evaluation": evaluation_text,
        }) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.post("/start")
async def start_scenario(scenario_id: str = Form(...)):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Ssenariy topilmadi")

    tag = opening_emotion_tag(scenario["personality"])
    opening = scenario["opening_line"]
    llm_text = opening if opening.strip().startswith("[") else f"{tag} {opening}"

    emotion, clean = extract_emotion(llm_text)
    audio_response = text_to_speech(clean)
    if audio_response:
        audio_response = apply_emotion_to_audio(audio_response, emotion)

    audio_base64 = base64.b64encode(audio_response).decode("utf-8") if audio_response else None

    return {"llm_text": llm_text, "audio_base64": audio_base64}


if __name__ == "__main__":
    import uvicorn

    info = check_ollama_model()
    if not info.get("ready"):
        print(f"⚠️  Ollama model topilmadi: {MODEL_NAME}")
        print(f"   Ishga tushiring: ollama pull {MODEL_NAME}")
    else:
        print(f"✓ Model tayyor: {MODEL_NAME}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
