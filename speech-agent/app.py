from flask import Flask, request, Response, send_from_directory, jsonify
import logging
import os
import requests
import base64
import hashlib
import time
from pathlib import Path

# Import knowledge base
from knowledge_base import get_knowledge_base

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize knowledge base
kb = get_knowledge_base()
kb.init_app(app)

# RunPod API endpoint
RUNPOD_API_ENDPOINT = os.getenv('RUNPOD_API_ENDPOINT')
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')


# Cache configuration
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)
# Default: 24 hours
CACHE_EXPIRATION = int(os.getenv('CACHE_EXPIRATION_SECONDS', 86400))


def get_cached_audio(text):
    """Get cached audio if available"""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{text_hash}.wav"
    meta_file = CACHE_DIR / f"{text_hash}.meta"
    
    if cache_file.exists() and meta_file.exists():
        # Check if cache is expired
        try:
            with open(meta_file, 'r') as f:
                timestamp = float(f.read().strip())
            
            if time.time() - timestamp <= CACHE_EXPIRATION:
                truncated = text[:50] + ('...' if len(text) > 50 else '')
                logging.info(f"Cache hit for: {truncated}")
                return cache_file.read_bytes()
            else:
                truncated = text[:50] + ('...' if len(text) > 50 else '')
                logging.info(f"Cache expired for: {truncated}")
                # Delete expired files
                cache_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
        except Exception as e:
            logging.error(f"Error reading cache metadata: {e}")
            # Delete corrupted files
            cache_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
    
    return None


def cache_audio(text, audio_data):
    """Cache audio data"""
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{text_hash}.wav"
    meta_file = CACHE_DIR / f"{text_hash}.meta"
    
    # Write audio data
    with open(cache_file, 'wb') as f:
        f.write(audio_data)
    
    # Write timestamp for expiration
    with open(meta_file, 'w') as f:
        f.write(str(time.time()))
    
    truncated = text[:50] + ('...' if len(text) > 50 else '')
    logging.info(f"Cached audio for: {truncated}")


def generate_tts_from_runpod(text):
    """Generate TTS using RunPod serverless API"""
    try:
        # Check cache first
        cached_audio = get_cached_audio(text)
        if cached_audio:
            return cached_audio
        
        # Call RunPod API
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"input": {"text": text}}
        
        truncated = text[:50] + ('...' if len(text) > 50 else '')
        logging.info(f"Calling RunPod API for: {truncated}")
        response = requests.post(
            RUNPOD_API_ENDPOINT, headers=headers, json=payload
        )
        
        if response.status_code != 200:
            logging.error(f"RunPod API error: {response.text}")
            raise Exception(f"RunPod API error: {response.status_code}")
        
        result = response.json()
        
        if "error" in result:
            logging.error(f"RunPod processing error: {result['error']}")
            raise Exception(result["error"])
        
        # Decode base64 audio
        audio_data = base64.b64decode(result["audio"])
        
        # Cache the result
        cache_audio(text, audio_data)
        
        return audio_data
    except Exception as e:
        logging.error(f"Error in TTS generation: {e}")
        raise


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/tts', methods=['POST'])
def text_to_speech():
    try:
        text = request.json.get('text', '')
        if not text:
            return "No text provided", 400
        if len(text) > 1000:  # Input validation
            return "Text too long. Maximum 1000 characters allowed.", 400
        
        # Generate audio
        audio_data = generate_tts_from_runpod(text)
        
        # Record the interaction in the knowledge base
        kb.record_interaction(
            query=text,
            response="[Audio response generated]",
            metadata={
                "type": "tts_request",
                "text_length": len(text),
                "audio_size": len(audio_data)
            }
        )
        
        return Response(audio_data, mimetype='audio/wav')
    except Exception as e:
        logging.error(f"Error in TTS endpoint: {e}")
        return "Internal server error", 500


@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Endpoint to clear the cache"""
    try:
        # Delete all files in cache directory
        count = 0
        for file in CACHE_DIR.glob('*'):
            file.unlink()
            count += 1
        
        logging.info(f"Cleared {count} files from cache")
        return {
            "success": True,
            "message": f"Cleared {count} files from cache"
        }, 200
    except Exception as e:
        logging.error(f"Error clearing cache: {e}")
        return {"success": False, "error": str(e)}, 500


@app.route('/knowledge', methods=['GET'])
def knowledge_dashboard():
    """Simple dashboard for the knowledge base"""
    return send_from_directory('.', 'knowledge.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
