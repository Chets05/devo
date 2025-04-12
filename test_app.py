from flask import Flask, request, jsonify, send_file
import logging
import sys
import os
import traceback

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Simple HTML with embedded JavaScript and debugging
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Form</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        .form-control { width: 100%; padding: 8px; box-sizing: border-box; }
        .btn { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        .result { margin-top: 20px; padding: 10px; border: 1px solid #ccc; display: none; }
        .error { color: #f44336; }
        .success { color: #4CAF50; }
        .debug { margin-top: 20px; padding: 10px; border: 1px solid #ccc; background: #f5f5f5; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Form</h1>
        
        <div class="form-group">
            <label for="topic">Enter a topic:</label>
            <input type="text" id="topic" class="form-control" value="test topic">
        </div>
        
        <button id="submitBtn" class="btn">Generate Video</button>
        <div id="loader" class="loader"></div>
        
        <div id="result" class="result"></div>
        
        <div class="debug">
            <h3>Debug Information</h3>
            <div id="debugInfo"></div>
        </div>
    </div>
    
    <script>
        // Add debug function
        function debugLog(message) {
            const debugInfo = document.getElementById('debugInfo');
            const timestamp = new Date().toISOString();
            const entry = document.createElement('div');
            entry.textContent = `${timestamp}: ${message}`;
            debugInfo.appendChild(entry);
            console.log(message);
        }
        
        document.getElementById('submitBtn').addEventListener('click', async function() {
            const topic = document.getElementById('topic').value;
            const result = document.getElementById('result');
            const loader = document.getElementById('loader');
            
            result.style.display = 'none';
            loader.style.display = 'block';
            
            debugLog(`Starting request for topic: "${topic}"`);
            
            try {
                // Log request details
                const requestData = { topic: topic };
                debugLog(`Request payload: ${JSON.stringify(requestData)}`);
                
                // First try to use fetch API
                debugLog('Sending request using fetch API...');
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                debugLog(`Response status: ${response.status}, ${response.statusText}`);
                
                if (response.ok) {
                    try {
                        // First try to handle as JSON
                        const responseText = await response.text();
                        debugLog(`Raw response: ${responseText.substring(0, 100)}${responseText.length > 100 ? '...' : ''}`);
                        
                        try {
                            const data = JSON.parse(responseText);
                            result.innerHTML = `<h3>Success!</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
                            result.className = 'result success';
                        } catch (parseError) {
                            debugLog(`Not a JSON response. Treating as plain text or binary.`);
                            result.innerHTML = `<h3>Success!</h3><p>Received non-JSON response (likely binary data)</p>`;
                            result.className = 'result success';
                        }
                    } catch (textError) {
                        debugLog(`Error reading response: ${textError.message}`);
                        result.innerHTML = `<h3>Error Reading Response</h3><p>${textError.message}</p>`;
                        result.className = 'result error';
                    }
                } else {
                    debugLog(`Request failed with status: ${response.status}`);
                    let errorText = `Status: ${response.status} ${response.statusText}`;
                    
                    try {
                        const errorData = await response.json();
                        debugLog(`Error response: ${JSON.stringify(errorData)}`);
                        errorText += `<br>Details: ${JSON.stringify(errorData)}`;
                    } catch (e) {
                        debugLog(`Error response wasn't JSON: ${e.message}`);
                    }
                    
                    result.innerHTML = `<h3>Request Failed</h3><p>${errorText}</p>`;
                    result.className = 'result error';
                }
            } catch (error) {
                debugLog(`Network error: ${error.message}`);
                result.innerHTML = `<h3>Network Error</h3><p>${error.message}</p><p>Check if the server is running and try again.</p>`;
                result.className = 'result error';
            } finally {
                loader.style.display = 'none';
                result.style.display = 'block';
            }
        });
        
        // Log initial page load
        debugLog('Page loaded successfully');
    </script>
</body>
</html>
"""

app = Flask(__name__)

@app.route('/')
def index():
    logger.info("Serving index page")
    return HTML

@app.route('/api/generate', methods=['POST', 'OPTIONS'])
def generate():
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
    logger.info(f"Raw data: {request.data.decode('utf-8') if request.data else 'No data'}")
    
    try:
        # Get topic from request
        if request.is_json:
            data = request.get_json()
            logger.info(f"JSON Data: {data}")
            
            if data and 'topic' in data:
                topic = data['topic']
            else:
                topic = 'default topic'
                logger.warning("No topic found in request, using default")
        else:
            # Try to get from form data
            topic = request.form.get('topic', 'default topic')
            logger.warning(f"Request wasn't JSON, extracted topic from form: {topic}")
        
        logger.info(f"Processing topic: {topic}")
        
        # Return a success response
        response_data = {
            'status': 'success',
            'message': f'Request processed for topic: {topic}',
            'topic': topic,
            'request_details': {
                'method': request.method,
                'content_type': request.content_type,
                'headers': dict([(k, v) for k, v in request.headers.items()]),
                'is_json': request.is_json,
                'path': request.path,
                'endpoint': request.endpoint
            }
        }
        logger.info(f"Sending success response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': error_msg, 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    logger.info("Starting test server on http://127.0.0.1:5000")
    logger.info("Available routes:")
    logger.info("  / - Test form")
    logger.info("  /api/generate - API endpoint (POST)")
    
    app.run(debug=True) 