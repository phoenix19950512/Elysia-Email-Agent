# type: ignore

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

# Create FastAPI app
app = FastAPI(
    title="Elysia Email AI Agent",
    description="API for Email AI Agent with email processing, meeting and file management capabilities",
    version="1.0.0"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

# Include API routes
app.include_router(router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Elysia Partners Email AI Agent API",
        "version": "1.0.0",
        "documentation": "/docs"
    }
