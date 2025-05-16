# type: ignore

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import json
import socketio
import uvicorn
from app.processors.email_processor import email_processor
from app.services.activity_service import activity_service
from app.services.dg_service import finish_deepgram, process_audio_chunk

# Import your routes
from app.api.routes import router as api_router

def setup_templates():
    """Set up template files if they don't exist"""
    template_dir = os.path.join("app", "templates")
    os.makedirs(template_dir, exist_ok=True)

    email_template_path = os.path.join(template_dir, "email_templates.json")
    if not os.path.exists(email_template_path):
        default_templates = [
            {
                "name": "General Reply",
                "subject": "RE: {original_subject}",
                "body": "Thank you for your email. I will review it and get back to you soon.<br><br>Best regards,<br>Elysia Partners"
            },
            {
                "name": "Meeting Confirmation",
                "subject": "RE: {original_subject}",
                "body": "I confirm that I will attend the meeting.<br><br>Best regards,<br>Elysia Partners"
            },
            {
                "name": "Out of Office",
                "subject": "RE: {original_subject}",
                "body": "Thank you for your email. I am currently out of the office and will respond upon my return.<br><br>Best regards,<br>Elysia Partners"
            }
        ]
        with open(email_template_path, "w") as f:
            json.dump(default_templates, f, indent=4)

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
        await asyncio.sleep(60)
        start_background_tasks()
        return True
    except Exception as e:
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Setting up Email AI Agent...")
    setup_templates()
    asyncio.create_task(verify_credentials())
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
    fastapi_app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")

    @fastapi_app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(frontend_build_path, "index.html"))

# Create Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# Wrap FastAPI with Socket.IO
socketio_app = socketio.ASGIApp(sio, fastapi_app)

async def activity_summary_emitter():
    """
    Background task: fetch & emit every 5 seconds to ALL connected clients.
    """
    while True:
        summary = activity_service.get_activity_summary('user123')
        # broadcast to everyone on the default namespace
        await sio.emit('activity_summary', summary)
        await asyncio.sleep(5)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    if not hasattr(sio, '_activity_task_started'):
        sio._activity_task_started = True
        sio.start_background_task(activity_summary_emitter)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    await finish_deepgram(sio=sio, sid=sid)

@sio.event
async def chat_message(sid, data):
    print(f"Received message from {sid}: {data['message']}")
    from app.services.ai_service import AIService
    ai_service = AIService()
    response = ai_service.process_chat_message(data['message'])
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
