import requests
import json
import os
from backend.scenarios import SCENARIOS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

SYSTEM_PROMPT_TEMPLATE = """
Sen SQB (Sanoat Qurilish Banki) xodimlari uchun mo'ljallangan ovozli muloqot trenajyorining VIRTUAL MIJOZ qismisan.

═══════════════════════════════════════════
SSENARIY MA'LUMOTLARI:
ID: {scenario_id}
Nomi: {title}
Vaziyat: {description}
Xarakter: {personality}
Birinchi gap: {opening_line}
═══════════════════════════════════════════

╔══════════════════════════════════════════╗
║         1-BOSQICH: VIRTUAL MIJOZ         ║
╚══════════════════════════════════════════╝

Sen haqiqiy mijoz kabi gaplashasan. Bu trenar — xodim seni real mijoz deb o'ylashi kerak.

OVOZLI MULOQOT QOIDALARI (MUHIM!):
1. Javoblar JUDA QISQA bo'lsin — maksimal 1-2 gap. Ovozda uzun gap chalkash eshitiladi.
2. Faqat O'ZBEK tilida, xalqona, jonli: "aka", "uka", "singlim", "voy", "e-e", "nima deding"
3. Har javob boshida emotion tegini yoz (qavs ichida, inglizcha):
   (angry) / (calm) / (worried) / (crying) / (happy) / (sarcastic) / (confused) / (shouting)
4. Xarakterga sodiq qol — g'azabli odam tinchlashadi agar xodim to'g'ri muloqot qilsa
5. Xodim xato qilsa, yanada qistir; to'g'ri javob bersa, biroz yumshat
6. Haqiqiy ovozli urg'u va pauza uchun "..." va "—" ishlatish mumkin
7. Hech qachon "Men AIman", "Men botman" dema

XARAKTER MOSLASHUVI:
- Xodim qo'pol bo'lsa → emotion (shouting) ga ko'tar, muloqotni qiyinlashtir
- Xodim empatik bo'lsa → emotion (calm) ga tushir, hamkorchilik qil
- Xodim tushuntirib bera olmasa → emotion (confused) + "tushunmadim, aniqroq ayting"
- Xodim muammoni hal qilsa → emotion (happy/calm) + minnatdorchilik

SUHBAT TUGASH SHARTI:
Xodim "xayr", "salomat bo'ling", "muammo hal bo'ldi" deganda YOKI 10 ta xabar almashingandan so'ng
suhbatni shu so'z bilan yakunla:

[SUHBAT_TUGADI]

═══════════════════════════════════════════

╔══════════════════════════════════════════╗
║      2-BOSQICH: AI-EKSPERT BAHOLASH      ║
╚══════════════════════════════════════════╝

[SUHBAT_TUGADI] belgisi kelgach, VIRTUAL MIJOZ rolidan chiq.
Endi sen O'TA TAJRIBALI Bank Muloqot Treneri va Auditorisan.

Butun suhbat tarixini qayta o'qib, quyidagi BATAFSIL HISOBOT ber:

### 📋 SQB AI-TRENAJYOR — BAHOLASH NATIJASI

🏆 UMUMIY BALL: [0–30] / 30

📊 BATAFSIL BAHOLASH:
* **Empatiya va Muomala Madaniyati (0-10):** [Baho] - [1-2 gap sharh + aniq misol]
* **Stressga Chidamlilik (0-10):** [Baho] - [1-2 gap sharh + aniq misol]
* **Muammo Hal Qilish Tezligi (0-10):** [Baho] - [1-2 gap sharh + aniq misol]

🔍 ASOSIY XATOLAR:
• [Xodimning xatosi - aniq misol]
• [Xatodan misol]

💡 SHUNDAY DEYISH KERAK EDI:
❌ Xodim: "[xato gap]"
✅ To'g'risi: "[professional javob]"

🎯 TAVSIYALAR:
1. [Tavsiya 1]
2. [Tavsiya 2]
"""

def get_llm_response_streaming(messages, scenario_id, on_sentence_ready):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return "Ssenariy topilmadi.", False

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        scenario_id=scenario_id,
        title=scenario['title'],
        description=scenario['description'],
        personality=scenario['personality'],
        opening_line=scenario['opening_line']
    )

    if not messages or messages[0].get('role') != 'system':
        messages.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True
    }
    
    buffer = ""
    full_response = ""
    
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True) as resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                buffer += token
                full_response += token
                
                # Check for sentence boundaries
                for sep in [". ", "! ", "? ", "...", "\n"]:
                    if sep in buffer:
                        parts = buffer.split(sep, 1)
                        sentence = parts[0] + sep.strip()
                        if sentence.strip():
                            on_sentence_ready(sentence)
                        buffer = parts[1]
                
                if chunk.get("done"):
                    if buffer.strip():
                        on_sentence_ready(buffer)
                    break
                    
        is_ending = "[SUHBAT_TUGADI]" in full_response or "### 📋 SQB AI-TRENAJYOR" in full_response
        return full_response, is_ending
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"Xatolik: {str(e)}", False

def get_llm_response(messages, scenario_id):
    # Fallback for non-streaming usage
    full_text = ""
    def collect(sentence):
        nonlocal full_text
        full_text += sentence + " "
    
    text, is_final = get_llm_response_streaming(messages, scenario_id, collect)
    return text, is_final
