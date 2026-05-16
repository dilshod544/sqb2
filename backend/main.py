from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.stt import transcribe_audio
from backend.llm import get_llm_response
from backend.tts import text_to_speech
from backend.scenarios import SCENARIOS
import json

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

@app.post("/process")
async def process_voice(
    audio: UploadFile = File(...),
    scenario_id: str = Form(...),
    history: str = Form(...) # JSON string
):
    audio_bytes = await audio.read()
    
    # 1. STT
    user_text = transcribe_audio(audio_bytes)
    if not user_text:
        return JSONResponse({"error": "Nutq aniqlanmadi"}, status_code=400)
    
    # 2. LLM
    chat_history = json.loads(history)
    chat_history.append({"role": "user", "content": user_text})
    
    llm_text, is_final = get_llm_response(chat_history, scenario_id)
    
    # 3. TTS (Only if not final evaluation or if we want evaluation to be spoken too)
    audio_response = None
    if llm_text:
        audio_response = text_to_speech(llm_text)
    
    # Return everything
    # Since we can't easily send both JSON and Audio in one response without complex multipart
    # We will return JSON with the text and a separate endpoint for the audio or base64
    import base64
    audio_base64 = base64.b64encode(audio_response).decode('utf-8') if audio_response else None
    
    return {
        "user_text": user_text,
        "llm_text": llm_text,
        "is_final": is_final,
        "audio_base64": audio_base64
    }

@app.post("/start")
async def start_scenario(scenario_id: str = Form(...)):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Ssenariy topilmadi")
    
    llm_text = scenario['opening_line']
    audio_response = text_to_speech(llm_text)
    
    import base64
    audio_base64 = base64.b64encode(audio_response).decode('utf-8') if audio_response else None
    
    return {
        "llm_text": llm_text,
        "audio_base64": audio_base64
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
