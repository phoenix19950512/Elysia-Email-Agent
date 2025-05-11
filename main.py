# type: ignore

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from app.auth.graph_auth import GraphAuth
import socketio
import uvicorn

# Import your routes
from app.api.routes import router as api_router

# Initialize FastAPI app
fastapi_app = FastAPI(
    title="Elysia Email AI Agent",
    version="1.0.0",
    description="API backend for Email AI Agent with chat, email processing, and activity tracking."
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

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def chat_message(sid, data):
    print(f"Received message from {sid}: {data['message']}")
    from app.services.ai_service import AIService
    ai_service = AIService()
    response = ai_service.process_chat_message(data['message'])
    await sio.emit('chat_response', {'response': response}, room=sid)

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

def verify_credentials():
    """Verify the Microsoft Graph credentials"""
    try:
        auth = GraphAuth()
        token = auth.get_token()
        print("\u2705 Microsoft Graph authentication successful.")
        return True
    except Exception as e:
        print(f"\u274C Microsoft Graph authentication failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up Email AI Agent...")
    setup_templates()

    if verify_credentials():
        print("\n--- Email AI Agent Ready ---")
        print("FastAPI Swagger docs: http://localhost:8000/docs")
        print("WebSocket: Listening on ws://localhost:8000")
        uvicorn.run(
            "main:socketio_app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    else:
        print("Authentication failed. Server not started.")