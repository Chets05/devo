from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate_video():
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    # Handle POST request
    try:
        # Print request data for debugging
        print("Request received")
        print("Content-Type:", request.headers.get('Content-Type'))
        print("Request data:", request.data)
        
        # Get topic from request
        data = request.get_json()
        print("JSON data:", data)
        
        if data and 'topic' in data:
            topic = data['topic']
        else:
            topic = 'Default topic'
            
        print(f"Topic: {topic}")
        
        # Return success response
        return jsonify({
            "status": "success", 
            "message": f"Request received for topic: {topic}. This is a test response.",
            "topic": topic
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Print which routes are available
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} - {rule}")
    
    # Run the app
    app.run(debug=True) 