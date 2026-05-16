import os
import re
import ssl
import tempfile

from pydub import AudioSegment

ssl._create_default_https_context = ssl._create_unverified_context

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

UZ_INITIAL_PROMPT = (
    "Salom, men SQB bank mijoziman. O'zbek tilida gapiryapman. "
    "Karta, pul, bankomat, kredit, ilova, hisob, o'tkazma haqida."
)

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    try:
        from faster_whisper import WhisperModel

        compute = "int8" if WHISPER_DEVICE == "cpu" else "float16"
        _model = ("faster", WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=compute))
    except ImportError:
        import whisper

        _model = ("openai", whisper.load_model(WHISPER_MODEL))
    return _model


def _normalize_uz(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if re.search(r"[а-яА-ЯёЁ]", text):
        text = re.sub(r"[а-яА-ЯёЁ]+", " ", text).strip()
    replacements = {
        "салом": "salom",
        "карта": "karta",
        "пул": "pul",
        "банк": "bank",
    }
    low = text.lower()
    for k, v in replacements.items():
        low = low.replace(k, v)
    return low if low else text


def transcribe_audio(audio_bytes: bytes) -> str:
    suffix = ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_webm:
        temp_webm.write(audio_bytes)
        webm_path = temp_webm.name

    wav_path = webm_path.replace(".webm", ".wav")
    try:
        audio = AudioSegment.from_file(webm_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")

        backend, model = _load_model()

        if backend == "faster":
            segments, _info = model.transcribe(
                wav_path,
                language="uz",
                initial_prompt=UZ_INITIAL_PROMPT,
                beam_size=3,
                best_of=1,
                temperature=0,
                vad_filter=True,
                condition_on_previous_text=True,
            )
            text = " ".join(s.text.strip() for s in segments).strip()
        else:
            result = model.transcribe(
                wav_path,
                language="uz",
                fp16=False,
                initial_prompt=UZ_INITIAL_PROMPT,
                beam_size=3,
                temperature=0,
                condition_on_previous_text=True,
            )
            text = result["text"].strip()

        return _normalize_uz(text)
    except Exception as e:
        print(f"STT Error: {e}")
        return ""
    finally:
        for path in [webm_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)
