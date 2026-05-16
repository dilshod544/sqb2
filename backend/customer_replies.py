"""LLM ishlamasa — tayyor o'zbekcha mijoz javoblari."""

from backend.scenarios import SCENARIOS


def _emotion_for(scenario_id: str) -> str:
    p = SCENARIOS.get(scenario_id, {}).get("personality", "").lower()
    if "g'azab" in p or "asabiy" in p or "janjal" in p:
        return "g'azab"
    if "shosh" in p or "xavotir" in p:
        return "vahima"
    if "charcha" in p or "xafa" in p:
        return "yig'i"
    return "g'azab"


def template_reply(scenario_id: str, user_text: str) -> str:
    s = SCENARIOS.get(scenario_id, {})
    title = s.get("title", "muammo")
    desc = s.get("description", "")
    em = _emotion_for(scenario_id)
    t = (user_text or "").lower()

    if any(w in t for w in ("ism", "famil", "kim siz", "identifikatsiya")):
        return f"[xotirjam] Ismim Anvar Rahimov, telefon +998901112233."

    if any(w in t for w in ("kut", "kutib", "qancha vaqt", "hali")):
        return f"[{em}] Qancha kutaman? {title} — hal qiling tezroq!"

    if any(w in t for w in ("tekshir", "ko'rib", "qarab", "tizim", "bir daqiqa")):
        return f"[{em}] Tekshiring tez! {desc.split('.')[0]} — pulim qayerda?"

    if any(w in t for w in ("uzr", "kechirasiz", "afsus")):
        return f"[kinoya] Uzr yetadi, ishni qiling. Nima bo'ldi oxiri?"

    if any(w in t for w in ("qaytar", "hal", "tuzat", "topildi", "yechildi")):
        return f"[quvonch] Yaxshi, rahmat. Boshqa muammo yo'q hozir."

    if any(w in t for w in ("pasport", "karta raqam", "pin", "kod")):
        return f"[xotirjam] Ha, 8600 **** 1234, pasport AB1234567."

    if any(w in t for w in ("boshqa", "sotish", "kredit taklif", "aksiya")):
        return f"[g'azab] Aka, avval {title}ni hal qiling! Boshqa gap keyin."

    if any(w in t for w in ("xayr", "salomat", "rahmat")):
        return f"[xotirjam] Xayr, muammo hal bo'lsin."

    return f"[{em}] Aka, {title} bo'yicha nima qildingiz? Tezroq javob bering!"
