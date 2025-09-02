from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

# Import custom modules
from api.router import router

# Memory optimization settings
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Indian Legal Assistant API",
    description="API for Indian legal assistant with Gemini integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include router
app.include_router(router)

# Serve the frontend static files
app.mount("/nyayadoot", StaticFiles(directory="../l-frontend/dist", html=True), name="frontend")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the Indian Legal Assistant API",
        "frontend": "Access the frontend at /nyayadoot"
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
