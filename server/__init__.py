import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from server.api.routes import register_routes

load_dotenv()


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
    )

    # Configure session cookies for cross-origin requests (Vercel → Render)
    # REQUIRED for cookies to work across different domains
    app.config.update(
        SESSION_COOKIE_SAMESITE='None',  # Allow cross-site cookies
        SESSION_COOKIE_SECURE=True,       # Require HTTPS (mandatory with SameSite=None)
        SESSION_COOKIE_HTTPONLY=True,     # Security: prevent JavaScript access
    )

    # Configure CORS to allow requests from Vercel frontend
    # Get allowed origins from environment variable or use default
    allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    # Clean up origins (remove empty strings)
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # Add root route for health checks (Render, etc.)
    @app.route("/", methods=["GET"])
    def root():
        return {"message": "Tiggy API Server", "status": "healthy"}, 200

    register_routes(app)

    return app
