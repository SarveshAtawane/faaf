import asyncio
import random
import string
import httpx
import websockets
import json
import time

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

NUM_BOTS = 50
TOTAL_MESSAGES = 1000  # Number of messages to send across all bots
MESSAGES_PER_SECOND = 50

CLIENT_TIMEOUT = httpx.Timeout(5.0)
CLIENT_LIMITS = httpx.Limits(max_connections=200)

bot_credentials = []       # (bot_id, email, password)
bot_sessions = []          # (bot_id, user_id, client, ws, users_list)


def random_string(length=6):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


async def create_bot(bot_id):
    async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT, limits=CLIENT_LIMITS) as client:
        name = f"Bot{bot_id}_{random_string()}"
        email = f"{name}@test.com"
        password = "password"

        print(f"[CREATE-{bot_id}] Creating account {email}")
        try:
            await client.post(f"{API_URL}/users/", json={
                "name": name,
                "email": email,
                "password": password
            })
        except httpx.HTTPStatusError:
            print(f"[CREATE-{bot_id}] Signup failed (may already exist)")

        bot_credentials.append((bot_id, email, password))


async def login_bot(bot_id, email, password):
    await asyncio.sleep(bot_id)  # stagger login by 1 sec each

    client = httpx.AsyncClient(timeout=CLIENT_TIMEOUT, limits=CLIENT_LIMITS)
    try:
        res = await client.post(f"{API_URL}/users/login", json={
            "email": email,
            "password": password
        })
        res.raise_for_status()
        user = res.json()
        user_id = user["id"]
        print(f"[LOGIN-{bot_id}] Logged in user_id={user_id}")

        res = await client.get(f"{API_URL}/users/")
        users = [u for u in res.json() if u["id"] != user_id]

        if not users:
            print(f"[BOT-{bot_id}] No one to message.")
            return

        ws = await websockets.connect(f"{WS_URL}/ws/{user_id}")

        async def receive_messages():
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    print(f"[BOT-{bot_id}] Received: {data}")
            except websockets.ConnectionClosed:
                print(f"[BOT-{bot_id}] WebSocket closed.")

        asyncio.create_task(receive_messages())
        bot_sessions.append((bot_id, user_id, client, ws, users))

    except Exception as e:
        print(f"[LOGIN-{bot_id}] Error: {e}")


async def global_message_sender():
    print(f"\n🚀 Starting global message sending at {MESSAGES_PER_SECOND} msg/sec...\n")
    delay = 1 / MESSAGES_PER_SECOND
    sent = 0

    while sent < TOTAL_MESSAGES:
        if not bot_sessions:
            await asyncio.sleep(1)
            continue

        bot_id, user_id, client, _, users = random.choice(bot_sessions)
        receiver = random.choice(users)

        try:
            await client.post(f"{API_URL}/messages/", json={
                "senderId": user_id,
                "receiverId": receiver["id"],
                "message": f"Bot-{bot_id} says hi!"
            })
            print(f"[SEND] Bot-{bot_id} ➜ {receiver['name']}")
            sent += 1
        except Exception as e:
            print(f"[SEND ERROR] Bot-{bot_id} failed to send: {e}")

        await asyncio.sleep(delay)

    print("✅ Finished sending messages.")


async def main():
    # Step 1: Create accounts slowly
    for bot_id in range(NUM_BOTS):
        await create_bot(bot_id)
        await asyncio.sleep(3)

    # Step 2: Login bots with 1 sec delay
    login_tasks = [
        login_bot(bot_id, email, password)
        for bot_id, email, password in bot_credentials
    ]
    await asyncio.gather(*login_tasks)

    # Step 3: Start global message sender at fixed rate
    await global_message_sender()

    # Cleanup
    for bot_id, _, client, ws, _ in bot_sessions:
        await ws.close()
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
