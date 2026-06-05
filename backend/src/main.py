# main.py
# To run this server:
# 1. Install the necessary libraries:
#    pip install fastapi "uvicorn[standard]" python-dotenv httpx
# 2. Create a file named .env in the same directory and add your API key:
#    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
# 3. Run the server from your terminal:
#    uvicorn main:app --reload

import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()
# Get the port from environment variables, defaulting to 8000
PORT = os.getenv("PORT", "8000")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Gemini API Secure Proxy",
    description="A FastAPI server to securely handle requests to the Gemini API.",
    version="1.0.0"
)

# --- CORS Configuration ---
# This allows your frontend (running on a different domain/port) to communicate with this server.
# In a production environment, you should restrict the origins to your actual frontend's domain.
origins = [
    "http://localhost",
    "http://localhost:3000",
    f"http://127.0.0.1:{PORT}",
    f"http://0.0.0.0:{PORT}",
    f"http://localhost:{PORT}",
    "https://localhost",
    f"https://127.0.0.1:{PORT}",
    f"https://localhost:{PORT}",
    "null",  # Often used for local file-based origins
    # Add your deployed frontend's URL here - Replit will provide an HTTPS URL
    "https://traveladvisor-ai.replit.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

templates = Jinja2Templates(directory=".")

# --- API Key and URL Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # This provides a clear error if the API key is missing from the .env file.
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please create a .env file.")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"


# --- Pydantic Models for Request/Response ---
# This defines the expected structure of the JSON data your frontend will send.
class PromptRequest(BaseModel):
    prompt: str

# Montar archivos estáticos
#app.mount("/dist", StaticFiles(directory="frontend/dist"), name="dist")
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
#app.mount("/assets", StaticFiles(directory="frontend/build/assets"), name="assets")

# Servir otros archivos estáticos de la build
@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("frontend/build/manifest.json")

@app.get("/favicon.ico")
async def serve_favicon():
    return FileResponse("frontend/build/favicon.ico")

# Ruta para servir la aplicación React
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    return FileResponse("frontend/build/index.html")

# --- Web server endpoints ---
#@app.get("/")
#def serve_home(request: Request):
#    return templates.TemplateResponse("index.html", context= {"request": request})

# --- API Endpoints ---
@app.get("/api")
def health():
    """A simple root endpoint to confirm the server is running."""
    return {"status": "FastAPI server is running"}

@app.post("/api/get-advice")
async def get_travel_advice(request: PromptRequest):
    """
    Receives a prompt from the frontend, sends it to the Gemini API,
    and returns the response.
    """
    # This is the payload structure required by the Gemini API
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": request.prompt}]
            }
        ]
    }

    # httpx is an asynchronous HTTP client, perfect for FastAPI
    async with httpx.AsyncClient() as client:
        try:
            # Make the asynchronous POST request to the Gemini API
            response = await client.post(
                GEMINI_API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60.0  # Set a timeout for the API call
            )

            # Raise an exception for bad responses (4xx or 5xx)
            response.raise_for_status()

            # Return the JSON response from Gemini directly to the frontend
            return response.json()

        except httpx.HTTPStatusError as e:
            # This catches errors returned by the Gemini API (e.g., bad request, auth error)
            print(f"HTTP error occurred: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from Gemini API: {e.response.text}"
            )
        except Exception as e:
            # This catches other errors (e.g., network issues, timeouts)
            print(f"An unexpected error occurred: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"An internal server error occurred: {str(e)}"
            )

# --- How to Run (for reference) ---
# In your terminal, navigate to the directory containing this file and run:
# uvicorn main:app --reload
# The server will be available at http://127.0.0.1:8000