from flask import Flask, Blueprint
from server.api.routes.root import root
from server.api.routes.auth import auth
from server.api.routes.user import user
from server.api.routes.chat import chat
from server.api.routes.recommendations import recommendations


def register_routes(app: Flask):
    api = Blueprint("api", __name__, url_prefix="/api")

    api.register_blueprint(root)
    api.register_blueprint(auth)
    api.register_blueprint(user)
    api.register_blueprint(chat)
    api.register_blueprint(recommendations)

    app.register_blueprint(api)
