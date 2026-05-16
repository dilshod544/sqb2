import json
import os
import re
import requests

from backend.scenarios import SCENARIOS
from backend.customer_replies import template_reply, _emotion_for
from backend.uz_text import is_garbage, normalize_customer_reply

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

# Qisqa prompt — uzun prompt kichik modelda "sizib" chiqadi
CUSTOMER_PROMPT = """Sen bank mijozisan. FAQAT bitta qator javob yoz.

Muammo: {description}
Kayfiyat: {personality}

Format: [g'azab] yoki [vahima] yoki [quvonch] yoki [xotirjam] — keyin 1-2 gap o'zbekcha.
Misol: [g'azab] Kartamdan pul ketdi, tez tekshiring!

QAT'IYAN YOZMA: baholash, ball, /10, inglizcha, ruscha, ko'p qator, ʻ belgisi.
"""

EVAL_PROMPT = """Bank xodimini bahola. O'zbekcha, qisqa:

📋 BAHOLASH NATIJASI
UMUMIY BALL: X / 30
1. Mijozga munosabat (0-10): X
2. Bosimga chidash (0-10): X
3. Muammoni hal qilish (0-10): X
❌ ENG KATTA XATO: ...
💡 3 TA MASLAHAT: ...
"""


def check_ollama_model() -> dict:
    try:
        r = requests.get(OLLAMA_URL.replace("/api/chat", "/api/tags"), timeout=5)
        tags = [m["name"] for m in r.json().get("models", [])]
        has_model = any(MODEL_NAME.split(":")[0] in t for t in tags)
        return {"configured": MODEL_NAME, "available": tags, "ready": has_model}
    except Exception as e:
        return {"configured": MODEL_NAME, "error": str(e), "ready": False}


def _build_customer_messages(messages, scenario_id):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return None, None

    history = [m for m in messages if m.get("role") in ("user", "assistant")][-6:]
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")

    system = CUSTOMER_PROMPT.format(
        description=scenario["description"],
        personality=scenario["personality"],
    )

    msgs = [{"role": "system", "content": system}]
    for m in history:
        role = "user" if m["role"] == "user" else "assistant"
        content = m["content"]
        if role == "user":
            content = f"Bank xodimi: {content}"
        else:
            content = re.sub(r"\[.*?\]", "", content).strip()[:120]
            content = f"Mijoz: {content}"
        msgs.append({"role": role, "content": content})

    msgs.append({
        "role": "user",
        "content": f"Bank xodimi: {last_user}\n\nBitta qator javob (format: [hissiyot] gap):",
    })
    return scenario, msgs


def get_customer_reply(messages, scenario_id: str) -> str:
    """Bitta toza mijoz javobi — stream yo'q, axlat chiqmaydi."""
    scenario, full_messages = _build_customer_messages(messages, scenario_id)
    if not scenario:
        return template_reply(scenario_id, "")

    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    em = _emotion_for(scenario_id)
    fallback = template_reply(scenario_id, last_user)

    payload = {
        "model": MODEL_NAME,
        "messages": full_messages,
        "stream": False,
        "options": {
            "temperature": 0.35,
            "num_predict": 70,
            "top_p": 0.8,
            "repeat_penalty": 1.35,
            "stop": ["\n", "Bank xodimi:", "Mijoz:", "Xodim:", "Sen:", "📋", "UMUMIY"],
        },
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        raw = resp.json()["message"]["content"].strip()
        clean = normalize_customer_reply(raw, default_emotion=em)
        if clean and not is_garbage(clean):
            return clean
        print(f"LLM rad etildi (axlat): {raw[:80]}...")
    except Exception as e:
        print(f"LLM xato: {e}")

    return fallback


def get_evaluation(messages, scenario_id: str) -> str:
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return ""

    history = [m for m in messages if m.get("role") in ("user", "assistant")][-12:]
    transcript = "\n".join(
        f"{'Xodim' if m['role'] == 'user' else 'Mijoz'}: {m['content'][:200]}"
        for m in history
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": EVAL_PROMPT},
            {"role": "user", "content": f"Suhbat:\n{transcript}\n\nBaholash:"},
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 320, "stop": ["\n\n\n"]},
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=90)
        resp.raise_for_status()
        text = resp.json()["message"]["content"].strip()
        if is_garbage(text) or len(text) < 50:
            return _static_evaluation(history)
        return text
    except Exception as e:
        print(f"Eval xato: {e}")
        return _static_evaluation(history)


def _static_evaluation(history) -> str:
    n = sum(1 for m in history if m["role"] == "user")
    score = min(28, 12 + n * 3)
    return f"""📋 BAHOLASH NATIJASI
UMUMIY BALL: {score} / 30

1. Mijozga munosabat (0-10): {min(9, 5 + n)}
2. Bosimga chidash (0-10): {min(9, 4 + n)}
3. Muammoni hal qilish (0-10): {min(9, 4 + n)}

❌ ENG KATTA XATO: Suhbatni chuqurroq davom ettiring.
💡 3 TA MASLAHAT:
1. Mijoz ismini qayta tasdiqlang
2. Muammoni aniq tushuntiring
3. Hal qilish muddatini ayting"""


# Eski API — main.py chaqiradi
def get_llm_response_streaming(messages, scenario_id, on_sentence_ready):
    reply = get_customer_reply(messages, scenario_id)
    on_sentence_ready(reply)
    return reply, False
