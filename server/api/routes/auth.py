from dotenv import load_dotenv
from flask import Blueprint, session, request
from server.database import get_database

load_dotenv()

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/login", methods=["POST"])
def login():
    db = get_database()
    payload = request.get_json()

    if "email" not in payload:
        return {"error": "Missing required field: 'chatId'."}, 400

    email = payload["email"]
    db_user = db.users.find_one({"email": email})

    if not db_user:
        # Redirects them to the setup
        return {"error": f"User with email {email} not found"}, 404

    session["userId"] = db_user["_id"]
    return {"message": "Login successful"}, 200

# @auth.route("/complete-user-login", methods=["POST"])
# def complete_user_login():
#     db = get_database()
#     payload = request.get_json()

    # email = payload["email"]
    # db_user = 
