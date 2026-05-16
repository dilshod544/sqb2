from gtts import gTTS
import os
import tempfile
import io

def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='uz')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        print(f"TTS Error: {e}")
        return None
