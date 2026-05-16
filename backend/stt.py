import whisper
import os
import tempfile
from pydub import AudioSegment
import io
import ssl

# Bypass SSL for model download
ssl._create_default_https_context = ssl._create_unverified_context

# tiny = tez (1-2 sek), base = o'rta (2-3 sek), small = sifatli (3-4 sek)
# Using "base" as a good middle ground
model = whisper.load_model("base")

def transcribe_audio(audio_bytes):
    # 1. Save original to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
        temp_webm.write(audio_bytes)
        webm_path = temp_webm.name

    # 2. Convert to 16kHz mono WAV using pydub
    wav_path = webm_path.replace(".webm", ".wav")
    try:
        audio = AudioSegment.from_file(webm_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")
        
        # 3. Transcribe with optimizations
        result = model.transcribe(
            wav_path,
            language="uz",
            fp16=False,      # CPU da tezroq
            beam_size=1,     # Greedy search — tezroq
            best_of=1,
            temperature=0,   # Deterministik
            condition_on_previous_text=False  # Kontekstsiz — tezroq
        )
        return result["text"].strip()
    except Exception as e:
        print(f"STT Error: {e}")
        return ""
    finally:
        # Cleanup
        for path in [webm_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)
