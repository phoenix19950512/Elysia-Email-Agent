# type: ignore

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import json
import socketio
import uvicorn
from app.processors.email_processor import email_processor
from app.services.dg_service import finish_deepgram, process_audio_chunk
from app.services.openai_service import openai_service

# Import your routes
from app.api.routes import router as api_router

async def start_email_processor():
    """Start the email processor"""
    await email_processor.start()

def start_background_tasks():
    """Start background tasks when FastAPI starts"""
    from threading import Thread
    
    def run_processor():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_email_processor())

    thread = Thread(target=run_processor, daemon=True)
    thread.start()

async def verify_credentials():
    """Verify the Microsoft Graph credentials"""
    try:
        await asyncio.sleep(400)
        start_background_tasks()
        return True
    except Exception as e:
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Setting up Email AI Agent...")
    # asyncio.create_task(verify_credentials())
    print("\n--- Email AI Agent Ready ---")
    print("FastAPI Swagger docs: http://localhost:8000/docs")
    print("WebSocket: Listening on ws://localhost:8000")
    yield

# Initialize FastAPI app
fastapi_app = FastAPI(
    title="Elysia Email AI Agent",
    version="1.0.0",
    description="API backend for Email AI Agent with chat, email processing, and activity tracking.",
    lifespan=lifespan
)

# Configure CORS
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
fastapi_app.include_router(api_router, prefix="/api")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve frontend React build if it exists
frontend_build_path = os.path.join(os.getcwd(), "dist")
if os.path.isdir(frontend_build_path):
    fastapi_app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_build_path, "assets")),
        name="assets",
    )

    @fastapi_app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(frontend_build_path, "index.html"))

    @fastapi_app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, full_path: str):
        """
        - If the path corresponds to a real file under dist, serve it.
        - Otherwise hand back index.html so React Router can take over.
        """
        file_path = os.path.join(frontend_build_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(frontend_build_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# Wrap FastAPI with Socket.IO
socketio_app = socketio.ASGIApp(sio, fastapi_app)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    await finish_deepgram(sio=sio, sid=sid)

@sio.event
async def chat_message(sid, data):
    print(f"Received message from {sid}: {data['message']}")
    response = await openai_service.process_chat_message(data['message'])
    await sio.emit('chat_response', {'response': response}, room=sid)

@sio.event
async def audio_chunk(sid, data: bytes):
    await process_audio_chunk(sio=sio, sid=sid, data=data)

if __name__ == "__main__":
    uvicorn.run(
        "main:socketio_app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
