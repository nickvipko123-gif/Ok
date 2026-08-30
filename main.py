import os
import html
import threading
import requests
import telebot
from telebot import types
from flask import Flask

# ==============================
# 1. KEEP-ALIVE SERVER
# ==============================
app = Flask('')

@app.route('/')
def home():
    return "Facebook Downloader Bot is running 24/7 on Render!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()

# ==============================
# 2. CẤU HÌNH BOT & EMOJI PREMIUM
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8906024187:AAGf_VqH8JGuJWZPRei5kYuuqzo86CkjuJQ")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# HÀM TẠO EMOJI PREMIUM AN TOÀN
def get_premium_emoji(emoji_id, fallback_emoji):
    if emoji_id and emoji_id.strip():
        return f'<tg-emoji emoji-id="{emoji_id.strip()}">{fallback_emoji}</tg-emoji>'
    return fallback_emoji

# ⚠️ THAY CHUỖI SỐ BÊN DƯỚI BẰNG CUSTOM_EMOJI_ID BẠN LẤY ĐƯỢC TỪ @getidsbot
# Nếu chưa có ID thì cứ để rỗng "" nó sẽ dùng Emoji tiêu chuẩn!
EMOJI_DOWN  = get_premium_emoji("5443127283898405358", "📥")
EMOJI_WARN  = get_premium_emoji("5447644880824181073", "⚠️")
EMOJI_CROSS = get_premium_emoji("5210952531676504517", "❌")
EMOJI_CHECK = get_premium_emoji("6132058351917344923", "✅")
EMOJI_VIDEO = get_premium_emoji("5231012545799666522", "🔍")
EMOJI_STAR  = get_premium_emoji("6244569929383679631", "⭐")

# HÀM GỬI TIN NHẮN AN TOÀN (NẾU DÍNH LỖI EMOJI SẼ TỰ CHUYỂN VỀ TEXT THƯỜNG)
def safe_send_message(chat_id, text, reply_to_id=None, reply_markup=None):
    try:
        if reply_to_id:
            return bot.send_message(chat_id, text, reply_to_message_id=reply_to_id, reply_markup=reply_markup)
        return bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        if "DOCUMENT_INVALID" in str(e) or "BUTTON_TYPE_INVALID" in str(e):
            # Tự động lọc sạch thẻ <tg-emoji> nếu ID bị hỏng
            clean_text = html.unescape(text)
            import re
            clean_text = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', clean_text)
            if reply_to_id:
                return bot.send_message(chat_id, clean_text, reply_to_message_id=reply_to_id, reply_markup=reply_markup)
            return bot.send_message(chat_id, clean_text, reply_markup=reply_markup)
        raise e

# ==============================
# 3. LỆNH /START
# ==============================
@bot.message_handler(commands=["start"])
def start_command(message):
    user_name = html.escape(message.from_user.first_name)
    welcome_msg = (
        f"{EMOJI_STAR} <b>XIN CHÀO {user_name.upper()}!</b>\n"
        "<code>─────────────────────────</code>\n"
        "Chào mừng bạn đến với <b>Bot Tải Video Facebook 24/7</b>.\n\n"
        "🚀 <b>CÁCH SỬ DỤNG:</b>\n"
        "Gửi lệnh theo cú pháp:\n"
        "<code>/downfb [Link Facebook]</code>\n\n"
        "📌 <b>Ví dụ:</b>\n"
        "<code>/downfb https://www.facebook.com/watch/?v=123456789</code>\n"
        "<code>─────────────────────────</code>\n"
        "✨ <i>Chúc bạn có trải nghiệm tuyệt vời!</i>"
    )
    safe_send_message(message.chat.id, welcome_msg, reply_to_id=message.message_id)

# ==============================
# 4. LỆNH /DOWNFB
# ==============================
@bot.message_handler(commands=["downfb"])
def downfb(message):
    chat_id = message.chat.id
    message_id = message.message_id

    parts = message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        msg = (
            f"{EMOJI_WARN} <b>Vui lòng nhập link Facebook!</b>\n\n"
            "Ví dụ:\n"
            "<code>/downfb https://facebook.com/...</code>"
        )
        safe_send_message(chat_id, msg, reply_to_id=message_id)
        return

    fb_url = parts[1].strip()

    api_url = (
        "https://silent-mud-7026.codeofsaladin.workers.dev/"
        "?url=" + requests.utils.quote(fb_url, safe="")
    )

    try:
        response = requests.get(api_url, timeout=30)
    except requests.RequestException:
        safe_send_message(chat_id, f"{EMOJI_CROSS} Không thể kết nối API.")
        return

    if response.status_code != 200:
        safe_send_message(chat_id, f"{EMOJI_CROSS} Không thể kết nối API.")
        return

    try:
        data_json = response.json()
    except ValueError:
        safe_send_message(chat_id, f"{EMOJI_CROSS} API trả về dữ liệu không hợp lệ.")
        return

    if not data_json.get("success") or not data_json.get("result"):
        safe_send_message(chat_id, f"{EMOJI_CROSS} Không tìm thấy video.")
        return

    data = data_json["result"]

    hd_url = data.get("hdUrl") or ""
    sd_url = data.get("sdUrl") or ""
    video_url = hd_url if hd_url else sd_url

    if not video_url:
        safe_send_message(chat_id, f"{EMOJI_CROSS} Không tìm thấy link video.")
        return

    video_id = html.escape(str(data.get("id", "Không có")))
    content = html.escape(str(data.get("content", "")))

    caption = (
        f"{EMOJI_DOWN} <b>FACEBOOK DOWNLOADER</b>\n"
        "┌───⭓\n"
        f"│» <b>ID:</b> <code>{video_id}</code>\n"
        f"│» <b>Nội dung:</b>\n│   {content}\n"
        f"│» {EMOJI_VIDEO} <b>HD:</b> {'✅ Có' if hd_url else '❌ Không'}\n"
        f"│» {EMOJI_VIDEO} <b>SD:</b> {'✅ Có' if sd_url else '❌ Không'}\n"
        "└─────────────\n"
        "<b>Chọn chất lượng bên dưới để tải.</b>"
    )

    # Nút bấm bắt buộc chỉ dùng Emoji Unicode tiêu chuẩn (Telegram cấm Emoji Premium trong InlineButton)
    keyboard = types.InlineKeyboardMarkup()
    hd_button_url = hd_url if hd_url else sd_url
    sd_button_url = sd_url if sd_url else hd_url

    keyboard.row(
        types.InlineKeyboardButton("🎥 Tải HD", url=hd_button_url),
        types.InlineKeyboardButton("🎥 Tải SD", url=sd_button_url)
    )

    try:
        bot.send_video(
            chat_id,
            video_url,
            caption=caption,
            parse_mode="HTML",
            supports_streaming=True,
            reply_markup=keyboard
        )
    except Exception as e:
        safe_send_message(chat_id, caption, reply_markup=keyboard)

    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

# ==============================
# 5. CHẠY CHƯƠNG TRÌNH
# ==============================
if __name__ == "__main__":
    keep_alive()

    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    print("🤖 Bot đang chạy trên Server Render 24/7...")
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
