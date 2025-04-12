from flask import Flask, render_template, request, send_file, jsonify, make_response
import os
import logging
import sys
import traceback

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
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    logger.info(f"Content-Type: {request.content_type}")
    if request.data:
        logger.info(f"Raw data: {request.data.decode('utf-8')}")
    
    # Just return a test response for now
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
        
        logger.info(f"Topic received: {topic}")
        
        # Return a test JSON response for now
        response_data = {
            "status": "success",
            "message": f"Successfully received topic: {topic}. Video generation is not implemented in this simplified version.",
            "topic": topic
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    logger.info("Starting server on http://127.0.0.1:5000")
    logger.info("Available routes:")
    logger.info("  / - Main page")
    logger.info("  /generate - Test endpoint (POST)")
    
    app.run(debug=True) 