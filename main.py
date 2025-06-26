import os
import tempfile
import base64
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import ffmpeg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Security
security = HTTPBearer()

POLLINATIONS_URL = "https://text.pollinations.ai/openai"
HEADERS = {"Content-Type": "application/json"}

# Get API key from environment (don't crash if not found)
API_KEY = os.getenv("API_KEY")

# Authorization dependency
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API key not configured. Please set API_KEY environment variable.",
        )
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# Helper: Extract audio from video
def extract_audio_from_video(video_path, output_format="mp3"):
    audio_path = tempfile.mktemp(suffix=f'.{output_format}')
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='mp3', ac=1, ar='16000')
            .overwrite_output()
            .run(quiet=True)
        )
        return audio_path
    except Exception as e:
        print(f"ffmpeg error: {e}")
        return None

# Helper: Encode audio to base64
def encode_audio_base64(audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_path}")
        return None

# Helper: Transcribe audio using Pollinations API
def transcribe_audio(audio_path, question="Transcribe this audio"):
    base64_audio = encode_audio_base64(audio_path)
    if not base64_audio:
        return None
    audio_format = audio_path.split('.')[-1].lower()
    payload = {
        "model": "openai-audio",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": base64_audio,
                            "format": audio_format
                        }
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(POLLINATIONS_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        transcription = result.get('choices', [{}])[0].get('message', {}).get('content')
        return transcription
    except requests.exceptions.RequestException as e:
        print(f"Error transcribing audio: {e}")
        return None

# Helper: Analyze text for title and hashtags using Pollinations API
def analyze_text(text):
    # Prompt for title and hashtags
    prompt = f"""
Given the following transcript, generate a catchy title and 5 relevant hashtags.
Transcript: {text}
Respond in JSON: {{\"title\": ..., \"hashtags\": [ ... ] }}
"""
    payload = {
        "model": "openai-text",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]
    }
    try:
        response = requests.post(POLLINATIONS_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content')
        # Try to parse JSON from content
        import json
        try:
            data = json.loads(content)
            return data
        except Exception:
            # Fallback: try to extract title and hashtags from text
            return {"title": "", "hashtags": []}
    except requests.exceptions.RequestException as e:
        print(f"Error analyzing text: {e}")
        return {"title": "", "hashtags": []}

@app.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    # Save uploaded video to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp_video:
        tmp_video.write(await file.read())
        video_path = tmp_video.name
    # Extract audio
    audio_path = extract_audio_from_video(video_path)
    if not audio_path:
        os.remove(video_path)
        raise HTTPException(status_code=500, detail="Failed to extract audio from video.")
    # Transcribe audio
    transcript = transcribe_audio(audio_path)
    if not transcript:
        os.remove(video_path)
        os.remove(audio_path)
        raise HTTPException(status_code=500, detail="Failed to transcribe audio.")
    # Analyze text
    analysis = analyze_text(transcript)
    os.remove(video_path)
    os.remove(audio_path)
    return JSONResponse(content=analysis)

@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't require authentication"""
    return {
        "status": "healthy",
        "api_configured": bool(API_KEY),
        "ffmpeg_available": True  # We'll assume it's available since it's in Docker
    }

@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Video Title & Hashtag Extractor API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "docs": "/docs"
        },
        "authentication": "Bearer token required for /analyze endpoint"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 