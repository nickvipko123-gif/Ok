import os
import re
import html
from flask import Flask, request
import telebot
from telebot import types

# ==============================
# CẤU HÌNH BOT & EMOJI PREMIUM
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8830994003:AAF_MOZR2FG-Hlmd8Ow6oHT80KBaSefCujw")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# DANH SÁCH ID ADMIN (Thay ID Telegram thật của bạn vào đây để nhận quyền quản trị)
ADMIN_IDS = [8622474075, 987654321]  # <--- ĐIỀN ID TELEGRAM CỦA BẠN VÀO ĐÂY

# HÀM TẠO EMOJI PREMIUM AN TOÀN
def get_premium_emoji(emoji_id, fallback_emoji):
    if emoji_id and emoji_id.strip():
        return f'<tg-emoji emoji-id="{emoji_id.strip()}">{fallback_emoji}</tg-emoji>'
    return fallback_emoji

# DANH SÁCH EMOJI ĐỘNG TOÀN BỘ HỆ THỐNG
EMOJI_SHOP   = get_premium_emoji("5312361253610475399", "🛒")
EMOJI_FILE   = get_premium_emoji("5345987742276797245", "📁")
EMOJI_BANK   = get_premium_emoji("5445353829304387411", "💳")
EMOJI_USER   = get_premium_emoji("6132058351917344923", "👤")
EMOJI_CHECK  = get_premium_emoji("5262832270573582269", "✅")
EMOJI_CROSS  = get_premium_emoji("5210952531676504517", "❌")
EMOJI_WARN   = get_premium_emoji("6132153107485827049", "⚠️")
EMOJI_DOWN   = get_premium_emoji("5443127283898405358", "📥")
EMOJI_MONEY  = get_premium_emoji("5224257782013769471", "💰")
EMOJI_ADMIN  = get_premium_emoji("5231012545799666522", "🛠️")
EMOJI_CART   = get_premium_emoji("5443127283898405358", "📦")

# HÀM GỬI TIN NHẮN AN TOÀN (TỰ ĐỘNG FIX LỖI EMOJI / PARSE MODE)
def safe_send_message(chat_id, text, reply_to_id=None, reply_markup=None):
    try:
        if reply_to_id:
            return bot.send_message(chat_id, text, reply_to_message_id=reply_to_id, reply_markup=reply_markup)
        return bot.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        if "DOCUMENT_INVALID" in str(e) or "BUTTON_TYPE_INVALID" in str(e) or "PEER_ID_INVALID" in str(e):
            clean_text = html.unescape(text)
            clean_text = re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', clean_text)
            if reply_to_id:
                return bot.send_message(chat_id, clean_text, reply_to_message_id=reply_to_id, reply_markup=reply_markup)
            return bot.send_message(chat_id, clean_text, reply_markup=reply_markup)
        raise e

# ==============================
# DATABASE GIẢ LẬP THÔNG MINH
# ==============================
users_db = {}  # {chat_id: {"balance": 0, "name": "...", "username": "..."}}
products_db = {
    "src_1": {"name": "Source Code Telegram Bot Bán Hàng", "price": 500000, "file_id": None},
    "src_2": {"name": "Source Code Web Shop Tự Động", "price": 1200000, "file_id": None}
}
files_db = []  # Lưu danh sách file hệ thống quản lý

# Lưu trạng thái tạm thời của Admin khi đang thao tác (ví dụ: đang nhập tên/giá sản phẩm mới)
admin_states = {}

# ==============================
# GIAO DIỆN NGƯỜI DÙNG & KHÁCH HÀNG
# ==============================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in users_db:
        users_db[chat_id] = {
            "balance": 0, 
            "name": message.from_user.first_name, 
            "username": message.from_user.username or "Không có"
        }

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_shop = types.InlineKeyboardButton(f"{EMOJI_SHOP} Mua Mã Nguồn", callback_data="menu_shop")
    btn_file = types.InlineKeyboardButton(f"{EMOJI_FILE} Kho File & Tài Liệu", callback_data="menu_files")
    btn_bank = types.InlineKeyboardButton(f"{EMOJI_BANK} Nạp Tiền Bank", callback_data="menu_bank")
    btn_info = types.InlineKeyboardButton(f"{EMOJI_USER} Tài Khoản Cá Nhân", callback_data="menu_info")
    markup.add(btn_shop, btn_file, btn_bank, btn_info)

    # Nếu là Admin thì hiển thị thêm nút Quản Trị Hệ Thống ngay bảng điều khiển chính
    if chat_id in ADMIN_IDS:
        btn_admin = types.InlineKeyboardButton(f"{EMOJI_ADMIN} 👑 Bảng Điều Khiển Admin", callback_data="admin_panel")
        markup.add(btn_admin)

    text = (
        f"{EMOJI_SHOP} <b>HỆ THỐNG BÁN MÃ NGUỒN & QUẢN LÝ TỰ ĐỘNG</b>\n\n"
        f"Chào mừng <b>{message.from_user.first_name}</b> đến với hệ thống dịch vụ số.\n"
        f"Vui lòng chọn tính năng bên dưới để bắt đầu giao dịch!"
    )
    safe_send_message(chat_id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    # 1. MENU CỬA HÀNG MÃ NGUỒN
    if data == "menu_shop":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p_id, prod in products_db.items():
            markup.add(types.InlineKeyboardButton(
                f"{EMOJI_CART} {prod['name']} — {prod['price']:,} VNĐ", 
                callback_data=f"buy_{p_id}"
            ))
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại", callback_data="back_home"))
        
        text = f"{EMOJI_SHOP} <b>DANH MỤC MÃ NGUỒN HIỆN CÓ</b>\n\nChọn mã nguồn bạn muốn mua bên dưới:"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # 2. XỬ LÝ MUA MÃ NGUỒN
    elif data.startswith("buy_"):
        p_id = data.replace("buy_", "")
        if p_id in products_db:
            prod = products_db[p_id]
            user_balance = users_db.get(chat_id, {}).get("balance", 0)
            
            if user_balance >= prod['price']:
                # Trừ tiền và giao dịch thành công
                users_db[chat_id]["balance"] -= prod['price']
                text = (
                    f"{EMOJI_CHECK} <b>GIAO DỊCH THÀNH CÔNG!</b>\n\n"
                    f"• Sản phẩm: <b>{prod['name']}</b>\n"
                    f"• Đã trừ: <b>{prod['price']:,} VNĐ</b>\n"
                    f"• Số dư còn lại: <b>{users_db[chat_id]['balance']:,} VNĐ</b>\n\n"
                    f"{EMOJI_DOWN} Liên hệ Admin hoặc nhận file nguồn tự động qua hệ thống kho file."
                )
            else:
                text = (
                    f"{EMOJI_CROSS} <b>SỐ DƯ KHÔNG ĐỦ!</b>\n\n"
                    f"• Sản phẩm: <b>{prod['name']}</b>\n"
                    f"• Giá tiền: <b>{prod['price']:,} VNĐ</b>\n"
                    f"• Số dư của bạn: <b>{user_balance:,} VNĐ</b>\n\n"
                    f"{EMOJI_WARN} Vui lòng nạp thêm tiền qua ngân hàng để tiếp tục mua hàng."
                )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"{EMOJI_BANK} Nạp Tiền Ngay", callback_data="menu_bank"))
            markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại cửa hàng", callback_data="menu_shop"))
            bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # 3. NẠP TIỀN QUA NGÂN HÀNG
    elif data == "menu_bank":
        text = (
            f"{EMOJI_BANK} <b>NẠP TIỀN TỰ ĐỘNG QUA NGÂN HÀNG</b>\n\n"
            f"• Ngân hàng: <b>MB Bank</b>\n"
            f"• Số tài khoản: <code>0123456789ABC</code>\n"
            f"• Chủ tài khoản: <b>NGUYEN VAN A</b>\n"
            f"• Nội dung chuyển khoản bắt buộc:\n"
            f"<code>NAP {chat_id}</code>\n\n"
            f"{EMOJI_WARN} Sau khi chuyển khoản xong, bấm vào nút bên dưới để báo cáo giao dịch cho hệ thống xét duyệt."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CHECK} Đã chuyển khoản, Xác Nhận Ngay", callback_data="confirm_bank"))
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại", callback_data="back_home"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data == "confirm_bank":
        # Gửi thông báo yêu cầu nạp tiền cho tất cả Admin
        user_info = users_db.get(chat_id, {})
        notify_text = (
            f"{EMOJI_WARN} <b>CÓ YÊU CẦU NẠP TIỀN MỚI!</b>\n\n"
            f"• Khách: {user_info.get('name')} (@{user_info.get('username')})\n"
            f"• ID: <code>{chat_id}</code>\n"
            f"• Nội dung yêu cầu: <code>NAP {chat_id}</code>\n\n"
            f"Bấm duyệt để cộng tiền cho khách:"
        )
        admin_markup = types.InlineKeyboardMarkup(row_width=2)
        admin_markup.add(
            types.InlineKeyboardButton(f"{EMOJI_CHECK} Cộng 50k", callback_data=f"approve_{chat_id}_50000"),
            types.InlineKeyboardButton(f"{EMOJI_CHECK} Cộng 100k", callback_data=f"approve_{chat_id}_100000"),
            types.InlineKeyboardButton(f"{EMOJI_CHECK} Cộng 200k", callback_data=f"approve_{chat_id}_200000"),
            types.InlineKeyboardButton(f"{EMOJI_CROSS} Từ chối", callback_data=f"reject_{chat_id}")
        )
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, notify_text, parse_mode="HTML", reply_markup=admin_markup)
            except:
                pass

        text = (
            f"{EMOJI_CHECK} <b>Đã gửi yêu cầu nạp tiền!</b>\n\n"
            f"Hệ thống đã chuyển thông tin chuyển khoản của bạn tới Quản trị viên. Số dư sẽ được cập nhật trong 1-3 phút."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại", callback_data="back_home"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # 4. ADMIN DUYỆT TIỀN CHO KHÁCH
    elif data.startswith("approve_") or data.startswith("reject_"):
        if chat_id not in ADMIN_IDS:
            return
        parts = data.split("_")
        action = parts[0]
        target_chat_id = int(parts[1])

        if action == "approve":
            amount = int(parts[2])
            if target_chat_id in users_db:
                users_db[target_chat_id]["balance"] += amount
            else:
                users_db[target_chat_id] = {"balance": amount, "name": "Khách", "username": ""}

            # Báo cho khách biết đã được cộng tiền
            try:
                bot.send_message(target_chat_id, f"{EMOJI_CHECK} Tài khoản của bạn đã được cộng thành công <b>{amount:,} VNĐ</b> vào số dư!", parse_mode="HTML")
            except:
                pass
            bot.edit_message_text(f"{EMOJI_CHECK} Đã duyệt cộng {amount:,} VNĐ cho user <code>{target_chat_id}</code> thành công!", chat_id, call.message.message_id, parse_mode="HTML")
        else:
            try:
                bot.send_message(target_chat_id, f"{EMOJI_CROSS} Yêu cầu nạp tiền của bạn đã bị từ chối hoặc sai nội dung chuyển khoản.", parse_mode="HTML")
            except:
                pass
            bot.edit_message_text(f"{EMOJI_CROSS} Đã từ chối giao dịch của user <code>{target_chat_id}</code>.", chat_id, call.message.message_id, parse_mode="HTML")

    # 5. THÔNG TIN TÀI KHOẢN
    elif data == "menu_info":
        user_data = users_db.get(chat_id, {"balance": 0})
        text = (
            f"{EMOJI_USER} <b>THÔNG TIN TÀI KHOẢN CỦA BẠN</b>\n\n"
            f"• ID Telegram: <code>{chat_id}</code>\n"
            f"• Tên: <b>{call.from_user.first_name}</b>\n"
            f"• Số dư hiện tại: {EMOJI_MONEY} <b>{user_data['balance']:,} VNĐ</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại", callback_data="back_home"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # 6. QUẢN LÝ FILE HỆ THỐNG
    elif data == "menu_files":
        file_list_str = ""
        if files_db:
            for idx, f_item in enumerate(files_db, 1):
                file_list_str += f"{idx}. File: <b>{f_item['name']}</b>\n"
        else:
            file_list_str = "Chưa có file nào được lưu trữ trên hệ thống."

        text = (
            f"{EMOJI_FILE} <b>KHO QUẢN LÝ FILE & TÀI LIỆU</b>\n\n"
            f"{file_list_str}\n\n"
            f"💡 <i>Gửi trực tiếp file tài liệu hoặc source code vào đoạn chat này để upload lên kho lưu trữ tự động.</i>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại", callback_data="back_home"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # 7. BẢNG ĐIỀU KHIỂN ADMIN PANEL
    elif data == "admin_panel":
        if chat_id not in ADMIN_IDS:
            return
        text = (
            f"{EMOJI_ADMIN} <b>BẢNG QUẢN TRỊ HỆ THỐNG (ADMIN)</b>\n\n"
            f"Quản lý mã nguồn, thêm sản phẩm mới hoặc xem thống kê doanh thu:"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"{EMOJI_SHOP} Quản lý sản phẩm mã nguồn", callback_data="admin_manage_products"))
        markup.add(types.InlineKeyboardButton(f"{EMOJI_FILE} Xem danh sách file hệ thống", callback_data="admin_manage_files"))
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Về trang chủ", callback_data="back_home"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data == "admin_manage_products":
        if chat_id not in ADMIN_IDS:
            return
        text = f"{EMOJI_SHOP} <b>QUẢN LÝ SẢN PHẨM MÃ NGUỒN</b>\n\nDanh sách mã nguồn hiện tại:"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p_id, prod in products_db.items():
            markup.add(types.InlineKeyboardButton(f"⚙️ {prod['name']} ({prod['price']:,}đ)", callback_data=f"admin_edit_{p_id}"))
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại Admin Panel", callback_data="admin_panel"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data == "admin_manage_files":
        if chat_id not in ADMIN_IDS:
            return
        text = f"{EMOJI_FILE} <b>KHO FILE TRÊN HỆ THỐNG ({len(files_db)} file)</b>\n\nTất cả file khách hoặc admin tải lên đều hiển thị ở đây."
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{EMOJI_CROSS} Quay lại Admin Panel", callback_data="admin_panel"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # 8. QUAY LẠI TRANG CHỦ
    elif data == "back_home":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_shop = types.InlineKeyboardButton(f"{EMOJI_SHOP} Mua Mã Nguồn", callback_data="menu_shop")
        btn_file = types.InlineKeyboardButton(f"{EMOJI_FILE} Kho File & Tài Liệu", callback_data="menu_files")
        btn_bank = types.InlineKeyboardButton(f"{EMOJI_BANK} Nạp Tiền Bank", callback_data="menu_bank")
        btn_info = types.InlineKeyboardButton(f"{EMOJI_USER} Tài Khoản Cá Nhân", callback_data="menu_info")
        markup.add(btn_shop, btn_file, btn_bank, btn_info)
        
        if chat_id in ADMIN_IDS:
            markup.add(types.InlineKeyboardButton(f"{EMOJI_ADMIN} 👑 Bảng Điều Khiển Admin", callback_data="admin_panel"))

        text = (
            f"{EMOJI_SHOP} <b>HỆ THỐNG BÁN MÃ NGUỒN & QUẢN LÝ TỰ ĐỘNG</b>\n\n"
            f"Chào mừng trở lại! Vui lòng chọn tính năng bên dưới."
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")


# ==============================
# TÍNH NĂNG NHẬN FILE TỰ ĐỘNG (UP FILE & QUẢN LÝ)
# ==============================
@bot.message_handler(content_types=['document', 'photo', 'video'])
def handle_docs(message):
    chat_id = message.chat.id
    file_name = "Không có tên"
    
    if message.document:
        file_name = message.document.file_name
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_name = "Hình ảnh tải lên"
    else:
        file_id = message.video.file_id
        file_name = "Video tải lên"

    # Lưu vào kho file hệ thống
    files_db.append({"chat_id": chat_id, "name": file_name, "file_id": file_id})

    text = (
        f"{EMOJI_CHECK} <b>LƯU TRỮ FILE THÀNH CÔNG!</b>\n\n"
        f"• Tên file: <b>{file_name}</b>\n"
        f"• Trạng thái: Đã được đưa vào kho lưu trữ an toàn của hệ thống."
    )
    safe_send_message(chat_id, text, reply_to_id=message.message_id)


# ==============================
# FLASK WEBHOOK (Chạy live 24/7 trên Render)
# ==============================
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return f"{EMOJI_CHECK} Bot is running live 24/7 on Render!", 200

if __name__ == "__main__":
    PORT = int(os.environ.get('PORT', 5000))
    bot.remove_webhook()
    
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    
    app.run(host="0.0.0.0", port=PORT)
