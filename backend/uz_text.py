import re

CYRILLIC = re.compile(r"[а-яА-ЯёЁ]")
EMOTION_TAG = re.compile(
    r"^\[(g'azab|yig'i|vahima|xotirjam|quvonch|kinoya|kulgi|hayrat)\]\s*",
    re.IGNORECASE,
)
GARBAGE_MARKERS = (
    "BAHOLASH", "Empatik", "Stressga", "QOIDALAR", "MISOL", "jonli:",
    "Xodim:", "Sen:", "UMUMIY BALL", "/10", "4-4-4", "ʻ ʻ",
    "tuzingki", "yuridika", "o'zga qilish",
)
REPEAT_CHAR = re.compile(r"(.)\1{4,}")
REPEAT_DIGIT = re.compile(r"(\d-\d-){3,}")


def clean_for_speech(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    text = CYRILLIC.sub("", text)
    text = text.replace("ʻ", "'").replace("'", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_garbage(text: str) -> bool:
    if not text or len(text.strip()) < 8:
        return True
    if len(text) > 220:
        return True
    if text.count("ʻ") > 1 or text.count("ʻ") + text.count("'") > 15:
        return True
    if REPEAT_CHAR.search(text):
        return True
    if REPEAT_DIGIT.search(text):
        return True
    if CYRILLIC.search(text):
        return True
    low = text.lower()
    if any(m.lower() in low for m in GARBAGE_MARKERS):
        return True
    if re.search(r"\d+\s*/\s*\d+", text):
        return True
    # Juda ko'p maxsus belgi
    if len(re.findall(r"[^\w\s',.!?+-]", text)) > 5:
        return True
    words = re.findall(r"[a-zA-Z'o']{2,}", text)
    if len(words) < 2:
        return True
    return False


def extract_first_customer_line(text: str) -> str:
    """Model chiqishidan faqat birinchi toza qatorni oladi."""
    text = text.replace("[SUHBAT_TUGADI]", "").strip()
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for line in lines:
        if not is_garbage(line):
            return line
    return ""


def normalize_customer_reply(text: str, default_emotion: str = "g'azab") -> str:
    line = extract_first_customer_line(text)
    if not line:
        return ""

    line = re.sub(r"\s+", " ", line).strip()
    if not EMOTION_TAG.match(line):
        line = f"[{default_emotion}] {line}"

    # Faqat birinchi gap (nuqtagacha)
    m = re.match(
        r"^(\[(?:g'azab|yig'i|vahima|xotirjam|quvonch|kinoya|kulgi|hayrat)\])\s*(.+)$",
        line,
        re.IGNORECASE,
    )
    if m:
        tag, body = m.group(1), m.group(2)
        for end in [". ", "! ", "? "]:
            idx = body.find(end)
            if idx != -1:
                body = body[: idx + 1]
                break
        if len(body) > 140:
            body = body[:140].rsplit(" ", 1)[0] + "!"
        line = f"{tag} {body.strip()}"

    return line if not is_garbage(line) else ""


def is_good_uzbek_reply(text: str) -> bool:
    return bool(normalize_customer_reply(text))
