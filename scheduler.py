from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from pyrogram import Client
from database import get_scheduled_files
import asyncio
import pytz

scheduler = BackgroundScheduler()

async def send_scheduled_files(bot):
    files = get_scheduled_files()
    now = datetime.now(pytz.utc)
    for file in files:
        if file['schedule_time'] <= now:
            try:
                await bot.send_document(
                    chat_id=file['channel_id'],
                    document=file['file_id'],
                    caption=file['caption']
                )
            except Exception as e:
                print("Error sending scheduled file:", e)

scheduler.add_job(lambda: asyncio.run(send_scheduled_files(Client('bot'))), 'interval', minutes=1)
scheduler.start()