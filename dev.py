import uvicorn
from main import verify_credentials, setup_templates

print("Setting up Email AI Agent...")
setup_templates()

if verify_credentials():
    print("\n--- Email AI Agent Ready ---")
    print("FastAPI Swagger docs: http://localhost:8000/docs")
    print("WebSocket: Listening on ws://localhost:8000")
    uvicorn.run(
        "main:socketio_app",
        host="0.0.0.0",
        port=10000,
        reload=False
    )
else:
    print("Authentication failed. Server not started.")