import os
from dotenv import load_dotenv
from flask import Blueprint, session

load_dotenv()

auth = Blueprint("auth", __name__, url_prefix="/auth")

@auth.route("/login", methods=["POST"])
def login():
    session["userId"] = os.getenv("MONGO_USER_ID")
    return {"message": "Login successful"}, 200
