import os
import html
import threading
import requests
import telebot
from telebot import types
from flask import Flask

# ==============================
# 1. TẠO WEB SERVER ĐỂ KEEP-ALIVE TRÊN RENDER
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
# 2. CẤU HÌNH BOT & MÃ EMOJI PREMIUM
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8906024187:AAHu8y2bf8WaZ55twhJz7rWld-jaolN3rgk")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Khai báo các ID Custom Emoji Premium
EMOJI_DOWN  = '<tg-emoji emoji-id="5368324170671202286">📥</tg-emoji>'
EMOJI_WARN  = '<tg-emoji emoji-id="5368324170671202291">⚠️</tg-emoji>'
EMOJI_CROSS = '<tg-emoji emoji-id="5368324170671202292">❌</tg-emoji>'
EMOJI_CHECK = '<tg-emoji emoji-id="5368324170671202289">✅</tg-emoji>'
EMOJI_VIDEO = '<tg-emoji emoji-id="5368324170671202287">🎥</tg-emoji>'
EMOJI_STAR  = '<tg-emoji emoji-id="5368324170671202290">⭐</tg-emoji>'

# ==============================
# 3. LỆNH /START (BỔ SUNG MỚI)
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
    bot.reply_to(message, welcome_msg, parse_mode="HTML")

# ==============================
# 4. LỆNH /DOWNFB
# ==============================
@bot.message_handler(commands=["downfb"])
def downfb(message):
    chat_id = message.chat.id
    message_id = message.message_id

    # LẤY LINK FACEBOOK
    parts = message.text.split(" ", 1)
    if len(parts) < 2 or not parts[1].strip():
        msg = (
            f"{EMOJI_WARN} <b>Vui lòng nhập link Facebook!</b>\n\n"
            "Ví dụ:\n"
            "<code>/downfb https://facebook.com/...</code>"
        )
        bot.reply_to(message, msg)
        return

    fb_url = parts[1].strip()

    # GỌI API FACEBOOK
    api_url = (
        "https://silent-mud-7026.codeofsaladin.workers.dev/"
        "?url=" + requests.utils.quote(fb_url, safe="")
    )

    try:
        response = requests.get(api_url, timeout=30)
    except requests.RequestException:
        bot.send_message(chat_id, f"{EMOJI_CROSS} Không thể kết nối API.")
        return

    if response.status_code != 200:
        bot.send_message(chat_id, f"{EMOJI_CROSS} Không thể kết nối API.")
        return

    try:
        data_json = response.json()
    except ValueError:
        bot.send_message(chat_id, f"{EMOJI_CROSS} API trả về dữ liệu không hợp lệ.")
        return

    if not data_json.get("success") or not data_json.get("result"):
        bot.send_message(chat_id, f"{EMOJI_CROSS} Không tìm thấy video.")
        return

    data = data_json["result"]

    # LẤY LINK VIDEO
    hd_url = data.get("hdUrl") or ""
    sd_url = data.get("sdUrl") or ""
    video_url = hd_url if hd_url else sd_url

    if not video_url:
        bot.send_message(chat_id, f"{EMOJI_CROSS} Không tìm thấy link video.")
        return

    # DATA PROCESSED
    video_id = html.escape(str(data.get("id", "Không có")))
    content = html.escape(str(data.get("content", "")))

    # CAPTION TRÌNH BÀY ĐẸP MẮT
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

    # INLINE KEYBOARD
    keyboard = types.InlineKeyboardMarkup()
    hd_button_url = hd_url if hd_url else sd_url
    sd_button_url = sd_url if sd_url else hd_url

    keyboard.row(
        types.InlineKeyboardButton("🎥 Tải HD", url=hd_button_url),
        types.InlineKeyboardButton("🎥 Tải SD", url=sd_button_url)
    )

    # KIỂM TRA DUNG LƯỢNG VIDEO
    size = 0
    try:
        head = requests.head(video_url, allow_redirects=True, timeout=15)
        content_length = head.headers.get("Content-Length")
        if content_length:
            size = int(content_length)
    except Exception:
        size = 0

    MAX_SIZE = 50 * 1024 * 1024  # 50 MB (Giới hạn Telegram Bot)

    # GỬI VIDEO HOẶC TIN NHẮN TẢI
    if size > MAX_SIZE:
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    else:
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
            print("send_video error:", e)
            try:
                bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
            except Exception as send_error:
                print("send_message error:", send_error)

    # XÓA LỆNH NGƯỜI DÙNG
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print("Không thể xóa message:", e)


# ==============================
# 5. CHẠY CHƯƠNG TRÌNH
# ==============================
if __name__ == "__main__":
    # Khởi chạy Web Server ngầm cho Render
    keep_alive()

    print("🤖 Bot đang chạy trên Server Render 24/7...")
    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
