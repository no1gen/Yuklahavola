# 🤖 Yukla Havola Bot — O'rnatish va Ishga Tushirish

## Bu nima?
Instagram, YouTube, TikTok, Facebook va 15+ platformadan
video/rasm yuklab beruvchi Telegram bot.  
✅ Obunasiz | ✅ Bepul | ✅ Cheksiz

---

## ⚡ TEZKOR O'RNATISH (5 daqiqa)

### 1-qadam: Bot token olish

1. Telegramda **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring
3. Botga nom bering: `Yukla Havola Bot`
4. Username bering: `YuklaHavola_bot`
5. BotFather sizga token beradi — uni saqlang:
   ```
   1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ
   ```

---

### 2-qadam: Python o'rnatish (agar yo'q bo'lsa)

```bash
# Ubuntu/Debian/VPS
sudo apt update
sudo apt install python3 python3-pip ffmpeg -y

# Windows
# python.org dan Python 3.11+ yuklab oling
# ffmpeg.org dan ffmpeg yuklab, PATH ga qo'shing
```

---

### 3-qadam: Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

---

### 4-qadam: Botni ishga tushirish

#### Linux / Mac / VPS:
```bash
export BOT_TOKEN="1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ"
python3 bot.py
```

#### Windows (CMD):
```cmd
set BOT_TOKEN=1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ
python bot.py
```

#### Windows (PowerShell):
```powershell
$env:BOT_TOKEN="1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ"
python bot.py
```

---

## 🌐 VPS da doimiy ishlatish (tavsiya etiladi)

### Render.com (BEPUL):
1. [render.com](https://render.com) da ro'yxatdan o'ting
2. GitHub ga bot kodini yuklang
3. "New Web Service" yarating
4. Build command: `pip install -r requirements.txt`
5. Start command: `python bot.py`
6. Environment variable qo'shing: `BOT_TOKEN = sizning_tokeningiz`

### Railway.app (BEPUL):
1. [railway.app](https://railway.app) — GitHub bilan login
2. "New Project" → "Deploy from GitHub"
3. Variables: `BOT_TOKEN = tokeningiz`

### Systemd (Ubuntu VPS):
```bash
# /etc/systemd/system/yuklabot.service
[Unit]
Description=Yukla Havola Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/yukla_havola_bot
Environment=BOT_TOKEN=SIZNING_TOKENINGIZ
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable yuklabot
sudo systemctl start yuklabot
sudo systemctl status yuklabot
```

---

## 📋 Bot buyruqlari

| Buyruq | Vazifa |
|--------|--------|
| `/start` | Botni boshlash |
| `/help` | Yordam |
| `/mp3 [havola]` | Faqat audio (MP3) yuklab olish |

---

## 🌍 Qo'llab-quvvatlanadigan platformalar

- 📸 Instagram (post, reel, story)
- ▶️ YouTube (video, shorts, playlist)
- 🎵 TikTok
- 👥 Facebook
- 🐦 Twitter / X
- 📌 Pinterest
- 💬 Reddit
- 🌐 VK, Odnoklassniki
- 🎮 Twitch
- 📺 Dailymotion
- Va 1000+ boshqa saytlar

---

## ❓ Ko'p so'raladigan savollar

**Savol: "Login required" xatosi chiqdi?**  
Javob: Instagram/Facebook ba'zi postlar uchun login talab qiladi.
Public (ochiq) postlar uchun ishlaydi.

**Savol: Fayl yuborilmaydi?**  
Javob: Fayl 50MB dan katta bo'lsa Telegram qabul qilmaydi.
YouTube da past sifat tanlang.

**Savol: Bot to'xtab qoldi?**  
Javob: VPS da systemd yoki screen ishlatib doimiy ishlating.

---

## 🔧 Texnik ma'lumot

- **Til:** Python 3.10+
- **Kutubxona:** python-telegram-bot 21, yt-dlp
- **Media:** FFmpeg (mp4 birlashtirish uchun)
- **Limit:** 50 MB (Telegram bepul limit)
