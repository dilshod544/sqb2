import re
import subprocess
import tempfile
import os

EMOTION_PARAMS = {
    "angry":    {"speed": 1.2, "volume": 1.4, "pitch": "+2st"},
    "shouting": {"speed": 1.3, "volume": 1.8, "pitch": "+3st"},
    "calm":     {"speed": 1.0, "volume": 1.0, "pitch": "0st"},
    "worried":  {"speed": 1.1, "volume": 0.9, "pitch": "+1st"},
    "crying":   {"speed": 0.85, "volume": 0.8, "pitch": "-1st"},
    "happy":    {"speed": 1.05, "volume": 1.1, "pitch": "+1st"},
    "sarcastic":{"speed": 0.9, "volume": 1.0, "pitch": "-1st"},
    "confused": {"speed": 0.95, "volume": 0.9, "pitch": "0st"},
}

def extract_emotion(text):
    # Match something like (angry) at the beginning or anywhere
    match = re.search(r'\((\w+)\)', text)
    if match:
        emotion = match.group(1).lower()
        # Remove the tag from the text
        clean_text = re.sub(r'\(.*?\)', '', text).strip()
        return emotion, clean_text
    return "calm", text

def apply_emotion_to_audio(audio_bytes, emotion):
    """ffmpeg orqali ovozga emotion parametrlarini qo'llash"""
    params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["calm"])
    
    # If it's calm/default, just return original
    if emotion == "calm" and params["speed"] == 1.0 and params["volume"] == 1.0:
        return audio_bytes

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as inp:
            inp.write(audio_bytes)
            inp_path = inp.name
        
        out_path = inp_path.replace(".mp3", "_emotion.mp3")
        
        # ffmpeg: tezlik va ovoz balandligini o'zgartirish
        # atempo faqat 0.5 dan 2.0 gacha ishlaydi. 
        # pitch o'zgartirish uchun rubberband yoki asetrate kerak, lekin soddalik uchun faqat tezlik va balandlikni qilamiz
        cmd = [
            "ffmpeg", "-y", "-i", inp_path,
            "-af", f"atempo={params['speed']},volume={params['volume']}",
            out_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        if os.path.exists(out_path):
            with open(out_path, "rb") as f:
                result = f.read()
            os.unlink(out_path)
        else:
            result = audio_bytes
            
        os.unlink(inp_path)
        return result
    except Exception as e:
        print(f"Emotion Audio Error: {e}")
        return audio_bytes
