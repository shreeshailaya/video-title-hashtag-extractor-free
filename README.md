# Video Analysis API

A FastAPI application that extracts audio from video files, transcribes the audio using Pollinations API, and generates titles and hashtags from the transcript.

## Features

- Extract audio from video files
- Speech-to-text transcription using Pollinations API
- Generate catchy titles and relevant hashtags
- Secure API key authentication
- Docker support for easy deployment

## Setup

### Option 1: Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg:**
   - Windows: Download from https://ffmpeg.org/download.html
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt install ffmpeg`

3. **Set up environment variables:**
   - Create a `.env` file with your API key:
   ```
   API_KEY=your_secret_api_key_here
   ```

4. **Run the server:**
   ```bash
   python main.py
   ```
   Or using uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

### Option 2: Docker Deployment

1. **Build and run with Docker:**
   ```bash
   # Build the image
   docker build -t video-analysis-api .
   
   # Run the container
   docker run -p 8000:8000 -e API_KEY=your_secret_api_key_here video-analysis-api
   ```

2. **Using Docker Compose (recommended):**
   ```bash
   # Set your API key in environment
   export API_KEY=your_secret_api_key_here
   
   # Or create .env file with API_KEY=your_secret_api_key_here
   
   # Start the service
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop the service
   docker-compose down
   ```

## API Usage

### Authentication
All endpoints require Bearer token authentication. Include your API key in the Authorization header:
```
Authorization: Bearer your_secret_api_key_here
```

### Endpoints

#### POST /analyze
Upload a video file to extract audio, transcribe it, and generate title/hashtags.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: video file
- Headers: Authorization: Bearer {your_api_key}

**Response:**
```json
{
  "title": "Generated catchy title",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"]
}
```

### Example Usage

#### Using curl:
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Authorization: Bearer your_secret_api_key_here" \
  -F "file=@your_video.mp4"
```

#### Using Python requests:
```python
import requests

url = "http://localhost:8000/analyze"
headers = {"Authorization": "Bearer your_secret_api_key_here"}
files = {"file": open("your_video.mp4", "rb")}

response = requests.post(url, headers=headers, files=files)
result = response.json()
print(f"Title: {result['title']}")
print(f"Hashtags: {result['hashtags']}")
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security

- API key is stored in `.env` file (not committed to version control)
- All endpoints require valid API key authentication
- Uses Bearer token authentication scheme
- Docker container runs as non-root user

## Error Handling

The API returns appropriate HTTP status codes:
- 401: Invalid or missing API key
- 500: Processing errors (audio extraction, transcription, or analysis failures)

## Docker Features

- Multi-stage build for optimized image size
- FFmpeg pre-installed in container
- Health checks for monitoring
- Non-root user for security
- Environment variable configuration
- Volume mounting for persistent storage (optional) 