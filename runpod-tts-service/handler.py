import runpod
from realtime_tts import RealTimeTTS
import base64
import logging
import time
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize model
try:
    logging.info("Initializing TTS model...")
    start_time = time.time()
    model = RealTimeTTS(
        model='canopylabs/orpheus-3b-0.1-pretrained',
        device='cuda'
    )
    init_time = time.time() - start_time
    logging.info(f"Model initialized in {init_time:.2f} seconds")
except Exception as e:
    logging.error(f"Failed to initialize model: {e}")
    logging.error(traceback.format_exc())
    raise


def handler(event):
    """
    RunPod serverless handler function
    """
    try:
        # Log request
        job_id = event.get("id", "unknown")
        logging.info(f"Processing job {job_id}")
        
        # Get text from the request
        if "input" not in event:
            logging.error(f"Job {job_id}: Missing input field")
            return {"error": "Missing input field"}
            
        if "text" not in event["input"]:
            logging.error(f"Job {job_id}: No text field in input")
            return {"error": "Missing text field in input"}
            
        text = event["input"]["text"]
        
        # Validate text
        if not text:
            logging.error(f"Job {job_id}: Empty text input")
            return {"error": "Invalid text input. Text cannot be empty."}
            
        if len(text) > 1000:
            text_len = len(text)
            logging.error(
                f"Job {job_id}: Text too long ({text_len} characters)"
            )
            return {
                "error": "Invalid text input. Maximum 1000 characters allowed."
            }
        
        # Log text summary
        truncated = text[:50] + ('...' if len(text) > 50 else '')
        logging.info(f"Job {job_id}: Processing text: {truncated}")
        
        # Generate audio
        start_time = time.time()
        audio_chunks = []
        
        try:
            for chunk in model.stream(text):
                audio_chunks.append(chunk)
        except Exception as e:
            err_msg = str(e)
            logging.error(
                f"Job {job_id}: Audio generation error: {err_msg}"
            )
            logging.error(traceback.format_exc())
            return {
                "error": f"Audio generation failed: {err_msg}"
            }
        
        # Combine audio chunks
        audio_data = b''.join(audio_chunks)
        
        # Log completion
        processing_time = time.time() - start_time
        audio_size = len(audio_data) / 1024  # KB
        logging.info(
            f"Job {job_id}: Generated {audio_size:.2f}KB "
            f"in {processing_time:.2f}s"
        )
        
        # Return base64 encoded audio
        return {
            "audio": base64.b64encode(audio_data).decode('utf-8'),
            "format": "wav",
            "meta": {
                "processing_time_seconds": processing_time,
                "audio_size_kb": audio_size
            }
        }
    except Exception as e:
        # Catch any unexpected errors
        error_msg = str(e)
        job = event.get('id', 'unknown')
        logging.error(
            f"Job {job}: Unexpected error: {error_msg}"
        )
        logging.error(traceback.format_exc())
        return {"error": error_msg}


# Start the serverless handler
runpod.serverless.start({"handler": handler})
