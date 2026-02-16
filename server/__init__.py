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

    # Configure CORS to allow requests from Vercel frontend
    # Get allowed origins from environment variable or use default
    allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # Add root route for health checks (Render, etc.)
    @app.route("/", methods=["GET"])
    def root():
        return {"message": "Tiggy API Server", "status": "healthy"}, 200

    register_routes(app)

    return app
