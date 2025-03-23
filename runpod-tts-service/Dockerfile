FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install runpod realtime_tts

# Install the Orpheus model
RUN pip install git+https://github.com/canopylabs/orpheus.git@3b-0.1-pretrained

# Copy handler code
COPY handler.py /app/handler.py

# Pre-download the model
RUN python -c "from realtime_tts import RealTimeTTS; tts = RealTimeTTS(model='canopylabs/orpheus-3b-0.1-pretrained', device='cuda')"

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# Start the handler
CMD ["python", "-u", "handler.py"]
