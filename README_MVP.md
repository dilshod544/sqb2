# SQB AI-Trenajyor MVP: To'liq Qo'llanma

Ushbu loyiha Bank xodimlari uchun Whisper STT, Qwen 2.5 LLM va gTTS texnologiyalariga asoslangan ovozli simulyatordir.

## 1. Tizim Talablari va Yuklab olish

Loyiha ishlashi uchun quyidagilarni o'rnatish kerak (men bularni allaqachon boshlaganman):

### A. Tizim paketlari (macOS):
```bash
brew install ffmpeg ollama
```

### B. Python kutubxonalari:
```bash
pip install fastapi uvicorn openai-whisper gtts python-multipart requests pydub
```

### C. Node.js paketlari (Frontend):
```bash
npm install
npm install -D tailwindcss postcss autoprefixer
```

---

## 2. Ishga Tushirish Tartibi (3 ta Terminalda)

### 1-TERMINAL: Ollama va Model
Ollama serverini yoqing va kerakli modelni yuklang:
```bash
brew services start ollama
# Modelni yuklash (4.7 GB, bir marta bajariladi)
ollama pull qwen2.5:7b-instruct
```

### 2-TERMINAL: Backend (Python API)
Loyiha mantiqini ishga tushiring:
```bash
# Loyiha asosiy papkasida
python3 -m backend.main
```
*Agar muvaffaqiyatli bo'lsa, `Uvicorn running on http://0.0.0.0:8000` xabarini ko'rasiz.*

### 3-TERMINAL: Frontend (Web)
Interfeysni ishga tushiring:
```bash
npm run dev
```
*Brauzerda `http://localhost:3000` manziliga kiring.*

---

## 3. Foydalanish Yo'riqnomasi

1.  Brauzerda ssenariylardan birini tanlang (masalan: **N-01: Pul yechilgan**).
2.  Mijoz muloqotni boshlaydi (ovozli va matnli).
3.  Javob berish uchun **Mikrofon** tugmasini bosing va gapiring.
4.  Gapirib bo'lgach, tugmani yana bir bor bosing (Stop).
5.  Tizim sizning gapingizni matnga o'giradi, LLMga yuboradi va mijoz javobini ovozli tarzda qaytaradi.
6.  Suhbat yakunlanganda (xayrlashganda), AI sizga avtomatik baho va tavsiyalar beradi.

---

## 4. Texnik Eslatmalar

*   **LLM**: Qwen 2.5 (7B) modeli lokal ishlaydi. 8GB+ RAM tavsiya etiladi.
*   **STT**: Whisper `base` modeli ishlatilmoqda. Agar aniqlik past bo'lsa, `backend/stt.py`da modelni `small`ga o'zgartirish mumkin.
*   **TTS**: gTTS internet talab qiladi. To'liq offline qilish uchun MeloTTSga o'tish rejalashtirilgan.
