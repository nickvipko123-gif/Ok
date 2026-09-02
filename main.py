import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8830994003:AAF_MOZR2FG-Hlmd8Ow6oHT80KBaSefCujw'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Hàm giả lập quá trình gọi API/Tool check acc Liên Quân thật
async def fetch_lien_quan_account(username: str, password: str) -> dict:
    # --- THAY THẾ PHẦN NÀY BẰNG CODE GỌI API/TOOL CHECK THỰC TẾ CỦA BẠN ---
    await asyncio.sleep(1.5) # Giả lập thời gian chờ request
    
    # Đây là dữ liệu trả về ĐẦY ĐỦ sau khi tool/API check thành công tài khoản
    return {
        "username": f"{username}:{password}",
        "name": "HuynhPro",
        "rank": "Kim Cương III",
        "star": 3,
        "level": 30,
        "qh": 12,
        "hero": 45,
        "skin": 62,
        "ban": "NO",
        "email": "NO [CHƯA XÁC THỰC]",
        "sdt": "NO",
        "cmnd": "NO",
        "authen": "NO",
        "fb": "NO",
        "so": 150,
        "quoc_gia": "VN",
        "login_cuoi": "18:30:15 02-09-2026",
        "ss": "3 [Butterfly Thánh nữ Khởi nguyên, Nakroth AIC, Tulen Tân Niên]",
        "sss": "1 [Violet Thần Long Hiệp Sĩ]",
        "anime": "1 [Kirito]",
        "other": "2 [Điêu Thuyền Tiệc Bãi Biển, Tel'Annas Cự Giải]",
        "trang_thai": "THÀNH CÔNG"
    }

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Gửi tài khoản theo định dạng <code>taikhoan:matkhau</code> để bot tiến hành check đầy đủ thông tin.",
        parse_mode="HTML"
    )

@dp.message_handler(regexp=r"^.+:.+$")
async def process_check_account(message: types.Message):
    raw_input = message.text.strip()
    parts = raw_input.split(":", 1)
    
    if len(parts) < 2:
        await message.reply("Sai định dạng! Vui lòng nhập theo mẫu: <code>taikhoan:matkhau</code>", parse_mode="HTML")
        return

    user, pwd = parts[0], parts[1]
    
    # Gửi tin nhắn thông báo đang check
    processing_msg = await message.reply("⏳ Đang kết nối hệ thống check acc Liên Quân, vui lòng đợi...", parse_mode="HTML")
    
    # Lấy dữ liệu đầy đủ từ hàm check
    acc_data = await fetch_lien_quan_account(user, pwd)

    # Format chuẩn đúng từng trường thông tin yêu cầu
    text = (
        f"<code>{acc_data['username']}</code>\n"
        f"| NAME : {acc_data['name']} "
        f"| RANK : {acc_data['rank']} [{acc_data['star']} ⭐] "
        f"| LEVEL : {acc_data['level']} "
        f"| QH : {acc_data['qh']} "
        f"| HERO : {acc_data['hero']} "
        f"| SKIN : {acc_data['skin']} "
        f"| BAN : {acc_data['ban']} "
        f"| EMAIL : {acc_data['email']} "
        f"| SDT : {acc_data['sdt']} "
        f"| CMND : {acc_data['cmnd']} "
        f"| AUTHEN : {acc_data['authen']} "
        f"| FB : {acc_data['fb']} "
        f"| SÒ : {acc_data['so']} "
        f"| QUỐC GIA : {acc_data['quoc_gia']} "
        f"| LOGIN LẦN CUỐI : {acc_data['login_cuoi']} "
        f"| SS : {acc_data['ss']} "
        f"| SSS : {acc_data['sss']} "
        f"| ANIME : {acc_data['anime']} "
        f"| OTHER : {acc_data['other']} "
        f"| TRẠNG THÁI : {acc_data['trang_thai']}"
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Check Lại", callback_data=f"recheck_{user}"))

    # Sửa lại tin nhắn chờ thành kết quả hoàn chỉnh
    await bot.edit_message_text(
        text=text,
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
