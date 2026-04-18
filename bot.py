#!/usr/bin/env python3
import os
import asyncio
import logging
import tempfile
import re
import shutil
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

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MAX_FILE_MB = 50
DOWNLOAD_DIR = tempfile.mkdtemp()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def detect_platform(url: str) -> str:
    u = url.lower()
    if "instagram.com" in u or "instagr.am" in u:
        return "Instagram"
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube"
    if "tiktok.com" in u:
        return "TikTok"
    if "facebook.com" in u or "fb.watch" in u:
        return "Facebook"
    if "twitter.com" in u or "x.com" in u:
        return "Twitter/X"
    if "pinterest.com" in u or "pin.it" in u:
        return "Pinterest"
    if "reddit.com" in u or "redd.it" in u:
        return "Reddit"
    if "vk.com" in u:
        return "VK"
    if "ok.ru" in u:
        return "OK.ru"
    return "Video"


def extract_url(text: str):
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0) if match else None


async def download_media(url: str, output_dir: str, audio_only: bool = False):
    files = []

    if audio_only:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(output_dir, "%(title).40s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        }
    else:
        ydl_opts = {
            "format": "best[ext=mp4]/best[height<=720][ext=mp4]/best[height<=720]/best",
            "outtmpl": os.path.join(output_dir, "%(title).40s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": MAX_FILE_MB * 1024 * 1024,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        }

    loop = asyncio.get_event_loop()

    def _do():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, _do)

    for f in Path(output_dir).iterdir():
        if f.is_file() and f.suffix not in [".part", ".json", ".ytdl"]:
            files.append(str(f))

    return files


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "🤖 <b>Yukla Havola Bot</b>\n\n"
        "📥 Qo'llab-quvvatlanadi:\n"
        "• 📸 Instagram (post, reel, story)\n"
        "• ▶️ YouTube\n"
        "• 🎵 TikTok\n"
        "• 👥 Facebook\n"
        "• 🐦 Twitter / X\n"
        "• 📌 Pinterest, Reddit, VK...\n\n"
        "✅ <b>Bepul, obunasiz!</b>\n\n"
        "👇 Havola yuboring:"
    )
    await update.message.reply_html(text)


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>Qo'llanma</b>\n\n"
        "• Havola yuboring — bot yuklab beradi\n"
        "• /mp3 [havola] — faqat audio MP3\n"
        "• /start — bosh menyu\n\n"
        "⚠️ Fayl 50MB dan oshmasligi kerak"
    )
    await update.message.reply_html(text)


async def mp3_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("❗ Misol: /mp3 https://youtu.be/...")
        return
    await process_download(update, ctx, ctx.args[0], audio_only=True)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url = extract_url(update.message.text.strip())
    if not url:
        await update.message.reply_text("🔗 Havola yuboring.\nMisol: https://www.instagram.com/reel/...")
        return
    await process_download(update, ctx, url)


async def process_download(update, ctx, url, audio_only=False):
    platform = detect_platform(url)
    mode = "🎵 Audio" if audio_only else "🎬 Video"

    status = await update.message.reply_html(
        f"⏳ <b>Yuklanmoqda...</b>\n"
        f"📡 {platform} | {mode}\n"
        f"<i>Biroz kuting...</i>"
    )

    tmp = tempfile.mkdtemp(dir=DOWNLOAD_DIR)

    try:
        files = await download_media(url, tmp, audio_only)

        if not files:
            await status.edit_text("❌ Fayl topilmadi. Havolani tekshiring.")
            return

        await status.edit_text(f"✅ Yuklandi! Yuborilmoqda...")

        for filepath in files[:4]:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if size_mb > MAX_FILE_MB:
                await update.message.reply_text(
                    f"⚠️ Fayl {size_mb:.1f} MB — juda katta (limit {MAX_FILE_MB} MB)."
                )
                continue

            ext = Path(filepath).suffix.lower()
            caption = f"📥 <b>Yukla Havola Bot</b> | {platform}"

            with open(filepath, "rb") as f:
                try:
                    if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp"]:
                        await update.message.reply_video(
                            video=f, caption=caption,
                            parse_mode="HTML", supports_streaming=True
                        )
                    elif ext in [".mp3", ".m4a", ".ogg", ".wav", ".aac", ".opus", ".webm"]:
                        await update.message.reply_audio(
                            audio=f, caption=caption, parse_mode="HTML"
                        )
                    elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        await update.message.reply_photo(
                            photo=f, caption=caption, parse_mode="HTML"
                        )
                    else:
                        await update.message.reply_document(
                            document=f, caption=caption, parse_mode="HTML"
                        )
                except Exception as e:
                    logger.error(f"Send error: {e}")
                    await update.message.reply_text("⚠️ Yuborishda xatolik.")

        try:
            await status.delete()
        except:
            pass

    except yt_dlp.utils.DownloadError as e:
        err = str(e).lower()
        if "private" in err or "login" in err or "sign in" in err:
            msg = "🔒 Bu kontent xususiy (private)."
        elif "unavailable" in err or "removed" in err:
            msg = "🚫 Kontent o'chirilgan yoki mavjud emas."
        elif "unsupported url" in err:
            msg = "❌ Bu platforma qo'llab-quvvatlanmaydi."
        elif "confirm you're not a bot" in err or "cookie" in err:
            msg = "🤖 YouTube bot deb blokladi. Boshqa havola yuboring."
        else:
            msg = f"❌ Yuklab bo'lmadi.\n<code>{str(e)[:150]}</code>"
        await status.edit_text(msg, parse_mode="HTML")

    except Exception as e:
        logger.exception(e)
        await status.edit_text("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("mp3", mp3_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Yukla Havola Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
