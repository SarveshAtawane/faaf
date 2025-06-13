from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import users, messages
from .core.websocket_manager import manager
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local testing, use "*" or replace with your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Make sure OPTIONS, POST, GET, etc., are allowed
    allow_headers=["*"],
)


# Mount static directory for frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("app/static/index.html")

# Include your routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(messages.router, prefix="/messages", tags=["Messages"])
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)