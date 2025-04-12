from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
import edge_tts
import json
import asyncio
import whisper_timestamped as whisper
import sys
import logging
import traceback
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "utility"))
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, search_pexels_videos, merge_empty_intervals
from utility.video.video_generator import create_video_from_videos

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Retrieve the API key from environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in environment variables.")

@app.route('/')
def index():
    logger.info("Serving index page")
    return render_template('index.html')

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate_video():
    # Log request details
    logger.info(f"Request received: {request.method}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        logger.info("Handling OPTIONS request")
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    logger.info(f"Content-Type: {request.content_type}")
    if request.data:
        logger.info(f"Raw data: {request.data.decode('utf-8')}")
    
    try:
        if not request.is_json:
            error_msg = "Request must be JSON"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400
            
        data = request.get_json()
        logger.info(f"JSON data received: {data}")
        
        if not data or 'topic' not in data:
            error_msg = "Topic is required"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400
            
        topic = data['topic']
        
        logger.info(f"Starting video generation for topic: {topic}")
        
        # Generate the script
        logger.info("Generating script...")
        try:
            response = generate_script(topic)
            logger.info("Script generated successfully")
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Error generating script: {str(e)}"}), 500

        # Generate audio from the script
        logger.info("Generating audio...")
        try:
            audio_path = generate_audio(response)
            logger.info(f"Audio generated successfully: {audio_path}")
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Error generating audio: {str(e)}"}), 500

        # Generate and save timed captions
        logger.info("Generating timed captions...")
        try:
            captions_timed = generate_timed_captions(audio_path)
            with open("captions_timed.txt", "w", encoding="utf-8") as f:
                f.write(str(captions_timed))
            logger.info("Timed captions generated successfully")
        except Exception as e:
            logger.error(f"Error generating captions: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Error generating captions: {str(e)}"}), 500

        # Get video search queries
        logger.info("Generating video search queries...")
        try:
            search_queries = getVideoSearchQueriesTimed(response, captions_timed)
        except Exception as e:
            logger.error(f"Error generating search queries: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Error generating search queries: {str(e)}"}), 500

        # Search for videos and create segments
        logger.info("Searching for videos...")
        try:
            segments = []
            for time_segment, queries in search_queries:
                url = None
                for query in queries:
                    url = search_pexels_videos(query)
                    if url:
                        break
                segments.append([time_segment, url])

            # Merge segments with no videos
            segments = merge_empty_intervals(segments)
        except Exception as e:
            logger.error(f"Error searching for videos: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Error searching for videos: {str(e)}"}), 500

        # Create the final video
        logger.info("Creating final video...")
        try:
            output_path = "rendered_video.mp4"
            create_video_from_videos(segments, audio_path, output_path)
            logger.info(f"Video rendering complete: {output_path}")
        except Exception as e:
            logger.error(f"Error creating video: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"Error creating video: {str(e)}"}), 500
        
        logger.info("Sending video file response")
        return send_file(output_path, mimetype='video/mp4')
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    logger.info("Starting server on http://127.0.0.1:5000")
    logger.info("Available routes:")
    logger.info("  / - Main page")
    logger.info("  /generate - Video generation endpoint (POST)")
    
    app.run(debug=True)
