import os

from flask import Flask
from dotenv import load_dotenv
from server.api.routes import register_routes

load_dotenv()


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
    )

    # Add root route for health checks (Render, etc.)
    @app.route("/", methods=["GET"])
    def root():
        return {"message": "Tiggy API Server", "status": "healthy"}, 200

    register_routes(app)

    return app
