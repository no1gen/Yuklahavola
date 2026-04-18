#!/usr/bin/env python3
"""
Yukla Havola Bot — Telegram bot
Instagram, YouTube, TikTok, Facebook va boshqa saytlardan media yuklab olish
Obunasiz, bepul, tez ishlaydi
"""

import os
import asyncio
import logging
import tempfile
import re
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ──────────────────────────────────────────────
# SOZLAMALAR — faqat shu yerni o'zgartiring
# ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8622971891:AAGBseU_gKtHL2SVQODQr0cV9984n2bwOYQ")
MAX_FILE_MB = 50          # Telegram bepul limit (MB)
DOWNLOAD_DIR = tempfile.mkdtemp()

# ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Qo'llab-quvvatlanadigan domenlar
SUPPORTED_DOMAINS = [
    "instagram.com", "instagr.am",
    "youtube.com", "youtu.be",
    "tiktok.com", "vm.tiktok.com",
    "facebook.com", "fb.com", "fb.watch",
    "twitter.com", "x.com", "t.co",
    "pinterest.com", "pin.it",
    "reddit.com", "redd.it",
    "vk.com",
    "dailymotion.com",
    "twitch.tv",
    "ok.ru",
]

def detect_platform(url: str) -> str:
    """URL'dan platformani aniqlash"""
    url_lower = url.lower()
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "Instagram"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    if "tiktok.com" in url_lower:
        return "TikTok"
    if "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "Facebook"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter/X"
    if "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "Pinterest"
    if "reddit.com" in url_lower or "redd.it" in url_lower:
        return "Reddit"
    if "vk.com" in url_lower:
        return "VKontakte"
    if "ok.ru" in url_lower:
        return "Odnoklassniki"
    return "Video/Audio"

def is_valid_url(text: str) -> bool:
    """URL to'g'riligini tekshirish"""
    pattern = re.compile(
        r"https?://[^\s]+"
    )
    return bool(pattern.search(text))

def extract_url(text: str) -> str | None:
    """Xabardан URL ni ajratib olish"""
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0) if match else None

async def download_media(url: str, output_dir: str, audio_only: bool = False) -> list[str]:
    """yt-dlp orqali media yuklash"""
    downloaded_files = []

    if audio_only:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_dir, "%(title).50s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True,
            "max_filesize": MAX_FILE_MB * 1024 * 1024,
        }
    else:
        ydl_opts = {
            "format": "best[ext=mp4]/best[height<=720]/best",
            "outtmpl": os.path.join(output_dir, "%(title).50s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "max_filesize": MAX_FILE_MB * 1024 * 1024,
            "writethumbnail": False,
            "writeinfojson": False,
        }

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, _download)

    # Yuklangan fayllarni topish
    for f in Path(output_dir).iterdir():
        if f.is_file() and not f.suffix in [".json", ".part"]:
            downloaded_files.append(str(f))

    return downloaded_files

# ──────────────────────────────────────────────
# HANDLERS
# ──────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/ start komandasi"""
    user = update.effective_user
    text = (
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "🤖 <b>Yukla Havola Bot</b> — tez va bepul media yuklovchi\n\n"
        "📥 <b>Qo'llab-quvvatlanadigan platformalar:</b>\n"
        "  • 📸 Instagram (post, reel, story)\n"
        "  • ▶️ YouTube (video, shorts)\n"
        "  • 🎵 TikTok\n"
        "  • 👥 Facebook\n"
        "  • 🐦 Twitter / X\n"
        "  • 📌 Pinterest\n"
        "  • 💬 Reddit\n"
        "  • 🌐 VK, OK va ko'plab boshqa saytlar\n\n"
        "✅ <b>Obunasiz, bepul, cheksiz!</b>\n\n"
        "👇 Shunchaki havola yuboring:"
    )
    keyboard = [
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help"),
         InlineKeyboardButton("📊 Statistika", callback_data="stats")]
    ]
    await update.message.reply_html(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/ help komandasi"""
    text = (
        "📖 <b>Yukla Havola Bot — Qo'llanma</b>\n\n"
        "1️⃣ Yuklamoqchi bo'lgan videoning havolasini nusxalang\n"
        "2️⃣ Shu havolani bot ga yuboring\n"
        "3️⃣ Bot avtomatik yuklab, sizga yuboradi\n\n"
        "🎵 <b>Faqat audio (MP3) yuklash:</b>\n"
        "  /mp3 [havola] — YouTube/boshqa saytdan audio\n\n"
        "📌 <b>Misol:</b>\n"
        "  <code>https://www.instagram.com/reel/...</code>\n"
        "  <code>https://youtu.be/...</code>\n"
        "  <code>https://vm.tiktok.com/...</code>\n\n"
        "⚠️ <b>Eslatma:</b> Fayl hajmi 50MB dan oshmasligi kerak\n\n"
        "🆘 Muammo bo'lsa: @your_support_username"
    )
    await update.message.reply_html(text)

async def mp3_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/ mp3 komandasi — faqat audio yuklash"""
    if not ctx.args:
        await update.message.reply_text("❗ Havola kiriting: /mp3 https://youtu.be/...")
        return
    url = ctx.args[0]
    await process_download(update, ctx, url, audio_only=True)

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Oddiy xabarni qayta ishlash"""
    text = update.message.text.strip()
    url = extract_url(text)

    if not url:
        await update.message.reply_text(
            "🔗 Iltimos, to'g'ri havola yuboring.\n"
            "Misol: https://www.instagram.com/reel/..."
        )
        return

    await process_download(update, ctx, url, audio_only=False)

async def process_download(
    update: Update,
    ctx: ContextTypes.DEFAULT_TYPE,
    url: str,
    audio_only: bool = False,
):
    """Asosiy yuklab olish jarayoni"""
    platform = detect_platform(url)
    mode = "🎵 Audio (MP3)" if audio_only else "🎬 Video"

    # Yuklanmoqda xabari
    status_msg = await update.message.reply_html(
        f"⏳ <b>Yuklanmoqda...</b>\n"
        f"📡 Platforma: <b>{platform}</b>\n"
        f"📦 Format: <b>{mode}</b>\n\n"
        f"<i>Biroz kuting...</i>"
    )

    tmp_dir = tempfile.mkdtemp(dir=DOWNLOAD_DIR)

    try:
        files = await download_media(url, tmp_dir, audio_only=audio_only)

        if not files:
            await status_msg.edit_text(
                "❌ Fayl topilmadi yoki yuklab bo'lmadi.\n"
                "🔄 Havolani tekshirib qayta urinib ko'ring."
            )
            return

        await status_msg.edit_text(
            f"✅ Yuklandi! Yuborilmoqda... ({len(files)} ta fayl)"
        )

        for filepath in files[:4]:  # Max 4 fayl
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

            if file_size_mb > MAX_FILE_MB:
                await update.message.reply_text(
                    f"⚠️ Fayl hajmi juda katta ({file_size_mb:.1f} MB).\n"
                    f"Telegram {MAX_FILE_MB} MB gacha qabul qiladi."
                )
                continue

            ext = Path(filepath).suffix.lower()
            caption = f"📥 <b>Yukla Havola Bot</b>\n🌐 {platform}"

            try:
                with open(filepath, "rb") as f:
                    if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
                        await update.message.reply_video(
                            video=f,
                            caption=caption,
                            parse_mode="HTML",
                            supports_streaming=True,
                        )
                    elif ext in [".mp3", ".m4a", ".ogg", ".wav", ".aac"]:
                        await update.message.reply_audio(
                            audio=f,
                            caption=caption,
                            parse_mode="HTML",
                        )
                    elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        await update.message.reply_photo(
                            photo=f,
                            caption=caption,
                            parse_mode="HTML",
                        )
                    else:
                        await update.message.reply_document(
                            document=f,
                            caption=caption,
                            parse_mode="HTML",
                        )
            except Exception as send_err:
                logger.error(f"Yuborish xatosi: {send_err}")
                await update.message.reply_text(
                    "⚠️ Fayl yuborishda xatolik. Qayta urinib ko'ring."
                )

        await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        err_text = str(e)
        if "login" in err_text.lower() or "private" in err_text.lower():
            msg = "🔒 Bu kontent xususiy (private) yoki kirish talab qiladi."
        elif "unavailable" in err_text.lower() or "removed" in err_text.lower():
            msg = "🚫 Kontent o'chirilgan yoki mavjud emas."
        elif "unsupported" in err_text.lower():
            msg = "❌ Bu platforma qo'llab-quvvatlanmaydi."
        else:
            msg = f"❌ Yuklab bo'lmadi.\nXato: {err_text[:200]}"

        await status_msg.edit_text(msg)

    except Exception as e:
        logger.exception(f"Kutilmagan xato: {e}")
        await status_msg.edit_text(
            "❌ Xatolik yuz berdi. Qayta urinib ko'ring yoki boshqa havola yuboring."
        )

    finally:
        # Vaqtinchalik fayllarni o'chirish
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Inline button callback"""
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        text = (
            "📖 <b>Qo'llanma</b>\n\n"
            "• Havola yuboring — bot yuklab beradi\n"
            "• /mp3 [havola] — faqat audio\n"
            "• /start — bosh menyu\n"
            "• /help — bu yordam"
        )
        await query.edit_message_text(text, parse_mode="HTML")
    elif query.data == "stats":
        await query.edit_message_text(
            "📊 <b>Bot statistikasi</b>\n\n"
            "✅ Bot ishlayapti!\n"
            "🌐 15+ platforma qo'llab-quvvatlanadi\n"
            "💯 Obunasiz, bepul",
            parse_mode="HTML"
        )

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN o'rnatilmagan!")
        print("   export BOT_TOKEN='your_token' qiling")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("mp3", mp3_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Yukla Havola Bot ishga tushdi!")
    print("   Telegram: @YuklaHavolaBot")
    print("   To'xtatish: Ctrl+C")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
