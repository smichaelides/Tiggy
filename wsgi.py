"""
WSGI entry point for Render deployment.
This file is used by gunicorn to serve the Flask application.
"""
from server import create_app

# Create the Flask app instance
app = create_app()

if __name__ == "__main__":
    # This allows running with: python wsgi.py
    app.run(host="0.0.0.0", port=5000, debug=False)
