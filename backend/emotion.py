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

UZBEK_EMOTION_MAP = {
    "g'azab": "angry",
    "yig'i": "crying",
    "vahima": "worried",
    "xotirjam": "calm",
    "quvonch": "happy",
    "kinoya": "sarcastic",
    "hayrat": "confused",
    "kulgi": "happy",
}

def opening_emotion_tag(personality: str) -> str:
    p = personality.lower()
    if any(x in p for x in ("g'azab", "asabiy", "janjal", "alam", "norozi")):
        return "[g'azab]"
    if any(x in p for x in ("xavotir", "shosh", "vahim")):
        return "[vahima]"
    if any(x in p for x in ("charcha", "xafa")):
        return "[yig'i]"
    if any(x in p for x in ("shubha", "ehtiyot")):
        return "[vahima]"
    if any(x in p for x in ("xursand", "muloyim")):
        return "[xotirjam]"
    return "[g'azab]"


def extract_emotion(text):
    uz_match = re.search(r"\[(g'azab|yig'i|vahima|xotirjam|quvonch|kinoya|hayrat|kulgi)\]", text)
    if uz_match:
        uz_tag = uz_match.group(1)
        emotion = UZBEK_EMOTION_MAP.get(uz_tag, "calm")
        clean_text = re.sub(r"\[.*?\]", "", text).strip()
        return emotion, clean_text

    en_match = re.search(r'\((\w+)\)', text)
    if en_match:
        emotion = en_match.group(1).lower()
        clean_text = re.sub(r'\(.*?\)', '', text).strip()
        return emotion, clean_text

    return "calm", text

def apply_emotion_to_audio(audio_bytes, emotion):
    """ffmpeg orqali ovozga emotion parametrlarini qo'llash"""
    params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["calm"])

    if emotion == "calm" and params["speed"] == 1.0 and params["volume"] == 1.0:
        return audio_bytes

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as inp:
            inp.write(audio_bytes)
            inp_path = inp.name

        out_path = inp_path.replace(".mp3", "_emotion.mp3")

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
