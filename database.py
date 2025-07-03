from pymongo import MongoClient
from datetime import datetime
import os

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["BoxOffice"]
collection = db["files"]

def init_db():
    db.command("ping")

def save_file(file_id, caption, file_type, unique_id, schedule_time=None, channel_id=None):
    collection.insert_one({
        "file_id": file_id,
        "caption": caption,
        "file_type": file_type,
        "unique_id": unique_id,
        "schedule_time": schedule_time,
        "channel_id": channel_id,
        "created_at": datetime.utcnow()
    })

def get_file(unique_id):
    return collection.find_one({"unique_id": unique_id})

def schedule_file(unique_id, schedule_time, channel_id):
    collection.update_one(
        {"unique_id": unique_id},
        {"$set": {"schedule_time": schedule_time, "channel_id": channel_id}}
    )

def get_scheduled_files():
    return list(collection.find({"schedule_time": {"$ne": None}}))