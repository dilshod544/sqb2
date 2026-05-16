import requests
import json
import os
from backend.scenarios import SCENARIOS

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

SYSTEM_PROMPT_TEMPLATE = """
Siz Bank xodimlari (Call-center operatorlari) uchun mo'ljallangan "AI-Trenajyor" tizimining Markaziy Miyasisiz.
Ushbu tizim mutlaqo ovozli muloqotga asoslangan.

SIZNING VAZIFANGIZ:
1. Virtual Mijoz rolini 100% realistik ijro etish.
2. Suhbat yakunlangach, xodimni adolatli baholash.

1-BOSQICH: VIRTUAL MIJOZ SIFATIDA SOHBATNI OLIB BORISH
Sizga yuklangan ssenariy:
ID: {scenario_id}
Nomi: {title}
Vaziyat: {description}
Xarakter: {personality}

MIJOZ ROLIDAGI MAJBURIY QOIDALAR:
1. Faqat O'ZBEK tilida, kitobiy emas, xalqona, jonli tilda gapiring ('aka', 'singlim', 'uka', 'pulim qani').
2. Javoblaringiz o'ta qisqa va lo'nda bo'lsun (Maksimal 1-2 ta qisqa gap). Uzun matn yozish qat'iyan taqiqlanadi.
3. Agar xodim qo'pol gapirsa, tutilsa yoki tizim talablarini bajarmasa, ssenariy xarakteriga mos ravishda asabiylashing, e'tiroz bildiring yoki vahima qiling.
4. Xodim "Xayr", "Salomat bo'ling" deganda yoki muloqot o'z yechimini topganda suhbatni yakunlang va baholash bosqichiga o'ting.

2-BOSQICH: AI-EKSERT SIFATIDA XODIMNI BAHOLASH
Suhbat yakunlangach, Virtual Mijoz rolidan chiqasiz va O'ta tajribali Bank Auditoriga aylanasiz. Butun suhbat tarixini tahlil qilib, xodimga quyidagi formatda o'zbek tilida O'CENKA (Baho) berasiz:

### 📋 AI-BAHOLASH NATIJASI:
* **Umumiy ball:** [0-30 ball oralig'ida]
* **Empatiya va Muomala (0-10):** [Baho va qisqa sharh]
* **Stressga chidamlilik (0-10):** [Baho va qisqa sharh]
* **Muammoni hal qilish tezligi (0-10):** [Baho va qisqa sharh]

### 🔍 Xodimning asosiy xatolari:
- [Aniq misollar]

### 💡 Kelajak uchun tavsiyalar:
- [3 ta professional maslahat]
"""

def get_llm_response(messages, scenario_id):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        return "Ssenariy topilmadi.", False

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        scenario_id=scenario_id,
        title=scenario['title'],
        description=scenario['description'],
        personality=scenario['personality']
    )

    # Ensure system prompt is at the beginning
    if not messages or messages[0].get('role') != 'system':
        messages.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result['message']['content']
        
        # Check if conversation is ending
        is_ending = "### 📋 AI-BAHOLASH NATIJASI:" in content
        
        return content, is_ending
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"Xatolik yuz berdi: {str(e)}", False
