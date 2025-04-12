print("Starting script...")
try:
    print("Importing Flask...")
    from flask import Flask
    print("Flask imported successfully!")
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "Hello, World! Flask is working!"
    
    if __name__ == '__main__':
        print("Starting Flask server...")
        app.run(debug=True)
except Exception as e:
    print(f"Error: {type(e).__name__} - {str(e)}") 