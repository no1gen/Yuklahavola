#!/usr/bin/env python3
import os
import asyncio
import logging
import tempfile
import re
import shutil
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# ─── SOZLAMALAR ───────────────────────────────
BOT_TOKEN    = os.getenv("BOT_TOKEN", "")
MAX_FILE_MB  = 49
TMPDIR       = tempfile.mkdtemp()
COOKIES_FILE = "/app/cookies.txt"   # GitHub da cookies.txt bo'lsa ishlaydi
# ──────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


def platform(url: str) -> str:
    u = url.lower()
    for kw, name in [
        ("instagram.com", "Instagram"), ("instagr.am", "Instagram"),
        ("youtu.be",      "YouTube"),   ("youtube.com",  "YouTube"),
        ("tiktok.com",    "TikTok"),
        ("facebook.com",  "Facebook"),  ("fb.watch",     "Facebook"),
        ("twitter.com",   "Twitter"),   ("x.com",        "Twitter"),
        ("pinterest.com", "Pinterest"), ("pin.it",       "Pinterest"),
        ("reddit.com",    "Reddit"),    ("redd.it",      "Reddit"),
        ("vk.com",        "VK"),        ("ok.ru",        "OK.ru"),
        ("twitch.tv",     "Twitch"),    ("dailymotion",  "Dailymotion"),
    ]:
        if kw in u:
            return name
    return "Video"


def get_url(text: str):
    m = re.search(r"https?://[^\s]+", text)
    return m.group(0) if m else None


def build_opts(out_dir: str, audio: bool) -> dict:
    has_cookie = os.path.exists(COOKIES_FILE)

    if audio:
        fmt = "bestaudio/best"
    else:
        fmt = (
            "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/"
            "best[ext=mp4][height<=720]/"
            "best[height<=720]/"
            "best"
        )

    opts = {
        "format":          fmt,
        "outtmpl":         os.path.join(out_dir, "%(title).50s.%(ext)s"),
        "quiet":           True,
        "no_warnings":     True,
        "noplaylist":      True,
        "max_filesize":    MAX_FILE_MB * 1024 * 1024,
        # YouTube bot-bypass
        "extractor_args":  {"youtube": {"player_client": ["android", "ios", "web"]}},
        # Agar ffmpeg mavjud bo'lsa birlashtiradi, bo'lmasa o'tkazib yuboradi
        "merge_output_format": "mp4",
        "postprocessor_args": ["-c", "copy"],
        # TikTok, Instagram watermark olib tashlash
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        },
    }

    if has_cookie:
        opts["cookiefile"] = COOKIES_FILE

    return opts


async def dl(url: str, out_dir: str, audio: bool) -> list[str]:
    loop = asyncio.get_event_loop()

    def _run():
        with yt_dlp.YoutubeDL(build_opts(out_dir, audio)) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, _run)

    return [
        str(f) for f in Path(out_dir).iterdir()
        if f.is_file() and f.suffix not in (".part", ".json", ".ytdl", ".png", ".jpg")
    ]


# ─── HANDLERS ────────────────────────────────

async def cmd_start(u: Update, _):
    ok = "✅ Cookie bor — Instagram ishlaydi!" if os.path.exists(COOKIES_FILE) \
         else "⚠️ Cookie yo'q — Instagram cheklangan"
    await u.message.reply_html(
        f"👋 Salom, <b>{u.effective_user.first_name}</b>!\n\n"
        "🤖 <b>Yukla Havola Bot</b>\n\n"
        "📥 <b>Qo'llab-quvvatlanadi:</b>\n"
        "  📸 Instagram • ▶️ YouTube • 🎵 TikTok\n"
        "  👥 Facebook • 🐦 Twitter/X • 📌 Pinterest\n"
        "  💬 Reddit • 🌐 VK • OK.ru • Twitch ...\n\n"
        f"{ok}\n\n"
        "✅ <b>Bepul · Obunasiz · Cheksiz</b>\n\n"
        "👇 Havola yuboring:"
    )


async def cmd_help(u: Update, _):
    await u.message.reply_html(
        "📖 <b>Qo'llanma</b>\n\n"
        "• Havola yuboring — video yuboriladi\n"
        "• /mp3 [havola] — faqat MP3 audio\n"
        "• /start — bosh menyu\n\n"
        "⚠️ Fayl 49 MB dan oshmasligi kerak\n\n"
        "<b>Instagram ishlamasa:</b>\n"
        "cookies.txt faylini GitHub ga yuklang"
    )


async def cmd_mp3(u: Update, ctx):
    if not ctx.args:
        await u.message.reply_text("❗ Misol: /mp3 https://youtu.be/...")
        return
    await process(u, ctx.args[0], audio=True)


async def msg_handler(u: Update, _):
    url = get_url(u.message.text or "")
    if not url:
        await u.message.reply_text("🔗 Havola yuboring.\nMisol: https://vm.tiktok.com/...")
        return
    await process(u, url, audio=False)


async def process(u: Update, url: str, audio: bool):
    plat = platform(url)
    mode = "🎵 Audio" if audio else "🎬 Video"

    st = await u.message.reply_html(
        f"⏳ <b>Yuklanmoqda...</b>\n"
        f"📡 {plat} | {mode}\n"
        "<i>Kuting...</i>"
    )

    tmp = tempfile.mkdtemp(dir=TMPDIR)
    try:
        files = await dl(url, tmp, audio)

        if not files:
            await st.edit_text("❌ Fayl topilmadi. Havolani tekshiring.")
            return

        await st.edit_text("✅ Yuklandi! Yuborilmoqda...")

        for fp in files[:5]:
            mb = os.path.getsize(fp) / 1024 / 1024
            if mb > MAX_FILE_MB:
                await u.message.reply_text(f"⚠️ {mb:.0f} MB — juda katta.")
                continue

            ext = Path(fp).suffix.lower()
            cap = f"📥 <b>Yukla Havola Bot</b> | {plat}"

            with open(fp, "rb") as fh:
                if ext in (".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp"):
                    await u.message.reply_video(fh, caption=cap, parse_mode="HTML",
                                                supports_streaming=True)
                elif ext in (".mp3", ".m4a", ".ogg", ".wav", ".aac", ".opus", ".flac"):
                    await u.message.reply_audio(fh, caption=cap, parse_mode="HTML")
                elif ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
                    await u.message.reply_photo(fh, caption=cap, parse_mode="HTML")
                else:
                    await u.message.reply_document(fh, caption=cap, parse_mode="HTML")

        try:
            await st.delete()
        except Exception:
            pass

    except yt_dlp.utils.DownloadError as e:
        err = str(e).lower()
        if any(k in err for k in ("private", "login required", "sign in", "not available")):
            if not os.path.exists(COOKIES_FILE):
                msg = (
                    "🔒 Bu platforma login talab qiladi.\n\n"
                    "<b>Instagram uchun yechim:</b>\n"
                    "1. Chrome da instagram.com ga kiring\n"
                    "2. <i>Get cookies.txt</i> extension o'rnating\n"
                    "3. Cookie export qiling → <code>cookies.txt</code>\n"
                    "4. GitHub ga yuklang (bot.py yoniga)"
                )
            else:
                msg = "🔒 Bu post xususiy (private) — hech qanday bot ocholmaydi."
        elif "bot" in err or "confirm" in err:
            msg = "🤖 Platforma vaqtincha blokladi. 1-2 daqiqa kutib qayta yuboring."
        elif "unsupported" in err:
            msg = "❌ Bu platforma qo'llab-quvvatlanmaydi."
        elif "removed" in err or "unavailable" in err or "deleted" in err:
            msg = "🚫 Kontent o'chirilgan yoki mavjud emas."
        elif "too large" in err or "filesize" in err:
            msg = "⚠️ Video juda katta (49 MB limitdan oshadi)."
        else:
            msg = f"❌ Xato:\n<code>{str(e)[:250]}</code>"
        await st.edit_text(msg, parse_mode="HTML")

    except Exception as e:
        log.exception(e)
        await st.edit_text("❌ Kutilmagan xatolik. Qayta urinib ko'ring.")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ─── MAIN ────────────────────────────────────

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN yo'q! Railway → Variables ga qo'shing.")
        return

    print("Cookie:", "✅ bor" if os.path.exists(COOKIES_FILE) else "⚠️ yo'q")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("mp3",   cmd_mp3))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))

    print("🚀 Yukla Havola Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
