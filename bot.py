import os
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

client = MongoClient(MONGO_URI)
db = client['BoxOfficeUploader']
files_col = db['files']

app = Client("BoxOfficeUploaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

ADMIN_ID = 7872708405
CHANNELS = {
    "@BoxOffice_Irani": -1002422139602,
    "@BoxOfficeMoviiie": -1002601782167,
    "@BoxOffice_Animation": -1002573288143
}

scheduler = AsyncIOScheduler()
scheduler.start()

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    args = message.text.split(" ")

    if len(args) > 1 and args[1].startswith("file_"):
        file_id = args[1].split("_")[1]
        file_doc = files_col.find_one({"file_key": file_id})
        if not file_doc:
            return await message.reply("❌ فایل مورد نظر پیدا نشد.")

        # ارسال پیام خوش‌آمدگویی فقط برای بار اول
        if db.users.find_one({"_id": user_id}) is None:
            db.users.insert_one({"_id": user_id})
            await message.reply_photo(
                photo="https://telegra.ph/file/7e73b95ddc9a700ea6a7a.jpg",
                caption="🎬 خوش اومدی به دنیای فیلم‌های خاص و نایاب! \nبرای دانلود فیلم مورد نظر آماده‌ای؟ 🎥🍿\n\n@BoxOfficeMoviiie @BoxOffice_Irani @BoxOffice_Animation"
            )

        sent = await message.reply_video(
            video=file_doc['file_id'],
            caption=file_doc['caption_short']
        )

        warn = await message.reply(
            "🚨 فقط 30 ثانیه وقت داری این فایل رو ذخیره یا ارسال کنی! بعدش پاک میشه! ⏳\n📥 سیو کن یا بفرست به یکی از چت‌هات سریع 💾🔥"
        )

        await asyncio.sleep(30)
        try:
            await sent.delete()
            await warn.delete()
        except:
            pass

    else:
        await message.reply("سلام! فایل خاصی برای نمایش موجود نیست. لطفاً از طریق لینک وارد بشید.")

@app.on_message(filters.video & filters.private & filters.user(ADMIN_ID))
async def handle_upload(client, message):
    video = message.video.file_id
    await message.reply("📄 لطفا کپشن کوتاه فایل را وارد کنید:")

    caption_msg = await app.listen(message.chat.id)
    caption = caption_msg.text

    await message.reply("⏰ لطفا تاریخ و زمان ارسال را وارد کن (مثال: 2025-07-03 18:00):")
    time_msg = await app.listen(message.chat.id)
    try:
        post_time = datetime.strptime(time_msg.text.strip(), "%Y-%m-%d %H:%M")
    except:
        return await message.reply("❌ فرمت زمان اشتباهه.")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1. BoxOffice_Irani", callback_data="ch_-1002422139602")],
        [InlineKeyboardButton("2. BoxOfficeMoviiie", callback_data="ch_-1002601782167")],
        [InlineKeyboardButton("3. BoxOffice_Animation", callback_data="ch_-1002573288143")]
    ])
    await message.reply("📢 لطفا کانال مقصد رو انتخاب کن:", reply_markup=keyboard)

    # گرفتن جواب از کاربر درباره کانال مقصد
    response = await app.listen(message.chat.id)
    if not response.text.startswith("ch_"):
        return await message.reply("❌ گزینه نامعتبره.")

    dest = int(response.text.split("_")[1])
    file_key = str(video)[-10:]

    files_col.insert_one({
        "file_id": video,
        "caption_short": caption,
        "post_time": post_time,
        "channel_id": dest,
        "file_key": file_key
    })

    await message.reply(
        f"✅ فایل ذخیره شد و در زمان تعیین‌شده ارسال میشه.\n📎 لینک اشتراک‌گذاری: `https://t.me/{client.me.username}?start=file_{file_key}`",
        quote=True
    )

    # زمان‌بندی ارسال
    scheduler.add_job(send_scheduled_post, 'date', run_date=post_time, args=[video, caption, dest])

async def send_scheduled_post(video_id, caption, dest):
    try:
        await app.send_video(dest, video=video_id, caption=caption)
    except Exception as e:
        print("❌ ارسال ناموفق:", e)

if __name__ == "__main__":
    app.run()
