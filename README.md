# Hybrid TTS System with DigitalOcean + RunPod Serverless

This project implements a hybrid text-to-speech (TTS) system using DigitalOcean for the web server component and RunPod Serverless for the GPU-intensive TTS processing.

## Architecture

The system consists of two main components:

1. **RunPod Serverless TTS Service**: Handles the GPU-intensive text-to-speech processing using the Orpheus model.
2. **Web Server (DigitalOcean)**: Provides the web interface, handles API requests, and implements caching to reduce redundant TTS processing.

## Benefits of the Hybrid Approach

- **Cost Efficiency**: Only pay for GPU resources when actually generating speech
- **Scalability**: Automatically scales with demand
- **Performance**: Fast response times with caching for repeated requests
- **Reliability**: Web server remains available even if TTS service is busy

## Components

### RunPod TTS Service
- Containerized service running on RunPod serverless
- Uses the Orpheus TTS model for high-quality speech synthesis
- Optimized for fast startup and efficient processing
- Returns base64-encoded audio data

### Web Server
- Lightweight Flask application running on DigitalOcean
- Provides a simple web interface for text input
- Implements file-based caching with expiration
- Handles API requests and proxies to RunPod when needed

## Deployment

### RunPod Deployment
1. Edit `deployment/deploy-runpod.sh` to set your Docker Hub username
2. Run the deployment script:
   ```
   chmod +x deployment/deploy-runpod.sh
   ./deployment/deploy-runpod.sh
   ```
3. Note the endpoint URL and API key for the next step

### DigitalOcean Deployment
1. Create a DigitalOcean droplet (Ubuntu 20.04 recommended)
2. Create a `.env` file with your RunPod endpoint and API key:
   ```
   RUNPOD_API_ENDPOINT=https://api.runpod.ai/v2/your-endpoint-id/run
   RUNPOD_API_KEY=your-runpod-api-key
   CACHE_EXPIRATION_SECONDS=86400
   ```
3. Edit `deployment/deploy-digitalocean.sh` to set your droplet's IP address
4. Run the deployment script:
   ```
   chmod +x deployment/deploy-digitalocean.sh
   ./deployment/deploy-digitalocean.sh
   ```

## Usage

Once deployed, you can access the web interface at `http://your-droplet-ip/`. Enter text in the input field and click "Play" to generate and hear the speech.

## Monitoring and Maintenance

- Check RunPod logs in the RunPod dashboard
- SSH into your DigitalOcean droplet to check logs:
  ```
  ssh root@your-droplet-ip
  cd /opt/speech-agent
  docker-compose logs
  ```
- Clear the cache if needed:
  ```
  curl -X POST http://your-droplet-ip/cache/clear
  ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
