from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from bson import ObjectId
from ..db.mongo import db
from ..models.message import MessageCreate, MessageOut
from ..core.websocket_manager import manager
from ..db.redis_client import redis_client
import json

router = APIRouter()


async def get_user_cached(user_id: str):
    cached = await redis_client.get(f"user:{user_id}")
    if cached:
        print(f"Cache hit for user {user_id}")
        return json.loads(cached)

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user_data = {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"]
        }
        await redis_client.set(f"user:{user_id}", json.dumps(user_data), ex=3600)
        return user_data
    return None

async def enrich_message(raw: dict) -> dict:
    sender_obj = await get_user_cached(raw['senderId'])
    receiver_obj = await get_user_cached(raw['receiverId'])

    return {
        "id": raw['id'],
        "senderId": raw['senderId'],
        "senderEmail": sender_obj['email'] if sender_obj else "",
        "senderName": sender_obj['name'] if sender_obj else "",
        "receiverId": raw['receiverId'],
        "receiverEmail": receiver_obj['email'] if receiver_obj else "",
        "receiverName": receiver_obj['name'] if receiver_obj else "",
        "message": raw['message'],
        "timestamp": raw['timestamp'],
    }

@router.post("/", response_model=MessageOut)
async def send_message(msg: MessageCreate):
    # Verify users exist
    for uid in (msg.senderId, msg.receiverId):
        if not await db.users.find_one({"_id": ObjectId(uid)}):
            raise HTTPException(status_code=404, detail=f"User {uid} not found")

    doc = msg.dict()
    ts = datetime.utcnow().isoformat()
    doc['timestamp'] = ts

    result = await db.messages.insert_one(doc)
    raw = {**doc, 'id': str(result.inserted_id)}

    enriched = await enrich_message(raw)
    # Push enriched message via WebSocket
    await manager.send_personal_message(enriched, msg.receiverId)
    return enriched

@router.get("/", response_model=List[MessageOut])
async def get_messages(userId: str):
    # Fetch last 50
    cursor = db.messages.find({
        "$or": [{"senderId": userId}, {"receiverId": userId}]
    }).sort("timestamp", -1).limit(50)

    enriched_list = []
    async for m in cursor:
        raw = {
            'id': str(m['_id']),
            'senderId': m['senderId'],
            'receiverId': m['receiverId'],
            'message': m['message'],
            'timestamp': m['timestamp'],
        }
        enriched_list.append(await enrich_message(raw))

    return list(reversed(enriched_list))  # oldest → newest
