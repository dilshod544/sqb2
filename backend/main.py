from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.stt import transcribe_audio
from backend.llm import get_llm_response_streaming, get_llm_response
from backend.tts import text_to_speech
from backend.scenarios import SCENARIOS
from backend.emotion import extract_emotion, apply_emotion_to_audio
import json
import base64
import asyncio
import threading
import queue
import time

app = FastAPI()

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/scenarios")
async def get_scenarios():
    return SCENARIOS

@app.post("/process-stream")
async def process_voice_stream(
    audio: UploadFile = File(...),
    scenario_id: str = Form(...),
    history: str = Form(...)
):
    audio_bytes = await audio.read()
    
    # 1. STT (Sync but we can run it here)
    user_text = transcribe_audio(audio_bytes)
    
    async def generate():
        # First, send the transcribed text
        yield json.dumps({"type": "stt", "text": user_text}) + "\n"
        
        chat_history = json.loads(history)
        chat_history.append({"role": "user", "content": user_text})
        
        full_llm_text = ""
        sentence_queue = queue.Queue()
        is_done_flag = [False] # Use a list to make it mutable in closure

        def on_sentence(sentence):
            nonlocal full_llm_text
            full_llm_text += sentence + " "
            
            emotion, clean = extract_emotion(sentence)
            clean = clean.replace("[SUHBAT_TUGADI]", "").strip()
            
            if not clean:
                return

            audio_data = text_to_speech(clean)
            audio_b64 = None
            if audio_data:
                # Apply emotion parameters via ffmpeg
                audio_with_emotion = apply_emotion_to_audio(audio_data, emotion)
                audio_b64 = base64.b64encode(audio_with_emotion).decode()
            
            sentence_queue.put({
                "type": "llm_chunk",
                "text": sentence,
                "emotion": emotion,
                "audio_base64": audio_b64
            })

        # Run LLM in a separate thread
        def run_llm():
            get_llm_response_streaming(chat_history, scenario_id, on_sentence)
            is_done_flag[0] = True

        thread = threading.Thread(target=run_llm)
        thread.start()

        # Stream results from queue
        while not is_done_flag[0] or not sentence_queue.empty():
            try:
                # Use a small timeout to not block too long
                item = sentence_queue.get(timeout=0.1)
                yield json.dumps(item) + "\n"
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue
        
        # Determine if it's the final evaluation
        is_final = "[SUHBAT_TUGADI]" in full_llm_text or "### 📋 SQB AI-TRENAJYOR" in full_llm_text
        yield json.dumps({"type": "done", "is_final": is_final}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.post("/start")
async def start_scenario(scenario_id: str = Form(...)):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Ssenariy topilmadi")
    
    llm_text = scenario['opening_line']
    audio_response = text_to_speech(llm_text)
    
    audio_base64 = base64.b64encode(audio_response).decode('utf-8') if audio_response else None
    
    return {
        "llm_text": llm_text,
        "audio_base64": audio_base64
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
