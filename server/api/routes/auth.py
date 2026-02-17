import logging
from dotenv import load_dotenv
from flask import Blueprint, session, request
from server.core.database import get_database
from server.api.models.user import User

load_dotenv()

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/login", methods=["POST"])
def login():
    db = get_database()
    payload = request.get_json()

    if "email" not in payload:
        return {"error": "Missing required field: 'email'."}, 400

    email = payload["email"]
    db_user = db.users.find_one({"email": email})

    if not db_user:
        # Redirects them to the setup
        return {"error": f"User with email {email} not found"}, 404

    session["userId"] = str(db_user["_id"])
    return {"message": "Login successful"}, 200

@auth.route("/complete-user-login", methods=["POST"])
def complete_user_login():
    db = get_database()
    payload = request.get_json()

    if "userData" not in payload:
        return {"error": "Missing required field: 'email'."}, 400

    user_data = payload["userData"]

    new_user = User(
        _id=user_data.get("email"),
        name=user_data.get("name"),
        email=user_data.get("email"),
        grade=user_data.get("grade"),
        concentration=user_data.get("concentration"),
        certificates=user_data.get("certificates", []),
        past_courses=user_data.get("past_courses", {}),  # Initialize as empty dict
    )

    try:
        result = db.users.insert_one(new_user.model_dump())
        # Set session after successful user creation
        # Note: _id is set to email, so inserted_id should be the email string
        session["userId"] = user_data.get("email")
    except Exception as ex:
        logging.error("Failed to create new user: %s", ex)
        return {"error": "Failed to create new user"}, 500

    return new_user.model_dump_json(), 201

@auth.route("/logout", methods=["POST"])
def logout():
    """Clear the user session on logout."""
    session.clear()
    return {"message": "Logout successful"}, 200
