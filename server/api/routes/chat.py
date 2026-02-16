import os
import logging
from dotenv import load_dotenv
from typing import Any
from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, request, session
from server.core.database import get_database
from server.api.models.chat import Chat
from server.api.models.message import UserMessage, ModelMessage
from server.llm.chat_prompts import build_chat_prompt
from server.llm.openai_service import generate_chat_response
from server.llm.context_manager import build_conversation_history

load_dotenv()

chat = Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/get-chat", methods=["GET"])
def get_chat():
    db = get_database()
    chat_id = request.args.get("chatId")
    user_id = session["userId"]

    if chat_id is None:
        return {"error": "Missing required fields: 'chatId' and 'userId'."}, 400

    try:
        chat_dict: dict[str, str | list[dict[str, str]]] | None | Any = (
            db.chats.find_one(
                {
                    "_id": ObjectId(chat_id),
                    "userId": user_id,
                }
            )
        )
        if not chat_dict:
            return {"error": "Chat not found."}, 404

        # Convert ObjectId fields to strings for JSON serialization
        chat_dict["_id"] = str(chat_dict["_id"])
        chat_dict["userId"] = str(chat_dict["userId"])

        for key in ["userMessages", "modelMessages"]:
            if isinstance(chat_dict[key], list):
                for msg in chat_dict[key]:
                    if (
                        isinstance(msg, dict)
                        and "userId" in msg
                        and isinstance(msg["userId"], ObjectId)
                    ):
                        msg["userId"] = str(msg["userId"])
                    if isinstance(msg, dict) and isinstance(msg["chatId"], ObjectId):
                        msg["chatId"] = str(msg["chatId"])
    except Exception as ex:
        logging.exception("Error retrieving chat data: %s", ex)
        return {"error": "Error retrieving chat data."}, 500

    return chat_dict, 200


@chat.route("/list-chats", methods=["GET"])
def list_chats():
    db = get_database()
    user_id = session["userId"]

    try:
        # only lists out the _id, counts, and timestamps; we can call /get-chat to get the messages
        # match by userId and return full documents
        chats = list(db.chats.find({"userId": user_id}))

        # normalize ObjectId fields to strings for JSON serialization
        for chat in chats:
            if isinstance(chat.get("_id"), ObjectId):
                chat["_id"] = str(chat["_id"])

            for key in ("userMessages", "modelMessages"):
                if not isinstance(chat.get(key), list):
                    continue

                for msg in chat[key]:
                    if isinstance(msg, dict):
                        if isinstance(msg.get("chatId"), ObjectId):
                            msg["chatId"] = str(msg["chatId"])
        # only lists out the _id, we can call /get-chat to get the messages
        for chat_dict in chats:
            chat_dict["_id"] = str(chat_dict["_id"])
    except Exception as ex:
        logging.exception("Error retrieving chats: %s", ex)
        return {"error": "Error retrieving chats."}, 500

    return {"chats": chats}, 200


@chat.route("/create-chat", methods=["POST"])
def create_chat():
    db = get_database()
    user_id = session.get("userId")
    
    if not user_id:
        return {"error": "User not authenticated"}, 401

    # Verify that userId exists in the users collection
    # Note: user _id is stored as email (string), not ObjectId
    try:
        # Try to find user by _id (which is the email)
        user_exists = db.users.find_one({"_id": user_id})
        
        # If not found, try with ObjectId (for backwards compatibility)
        if not user_exists:
            try:
                user_exists = db.users.find_one({"_id": ObjectId(user_id)})
            except (ValueError, TypeError):
                # user_id is not a valid ObjectId, probably an email - that's fine
                pass
        
        if not user_exists:
            logging.error("User with userId %s does not exist.", user_id)
            return {"error": "Invalid userId. User does not exist."}, 400
    except Exception as ex:
        logging.error("Failed to verify user existence: %s", ex)
        return {"error": f"Failed to verify user existence: {ex}"}, 500

    now = datetime.now(tz=timezone.utc)
    new_chat = Chat.model_validate(
        {
            "userId": user_id,
            "userMessages": [],
            "modelMessages": [],
            "createdAt": now,
            "updatedAt": now,
        }
    )

    try:
        chatId = db.chats.insert_one(new_chat.model_dump()).inserted_id
    except Exception as ex:
        logging.error("Failed to create a new chat: %s", ex)
        return {"error": f"Failed to create a new chat {ex}"}, 500

    response_data = new_chat.model_dump()
    response_data["_id"] = str(chatId)
    return response_data, 201


@chat.route("/delete-chat", methods=["DELETE"])
def delete_chat():
    db = get_database()
    user_id = session["userId"]
    payload = request.get_json()

    if "chatId" not in payload:
        return {"error": "Missing required field: 'chatId'."}, 400

    chatId = payload["chatId"]

    # Verify that userId exists in the users collection
    try:
        result = db.chats.delete_one({"userId": user_id, "_id": ObjectId(chatId)})
        if result.deleted_count == 0:
            error = (
                "Could not delete chat with userId %s and chatId %s",
                user_id,
                chatId,
            )
            logging.error(error)
            return {"error": error}, 500
    except Exception as ex:
        error = (
            "Error deleting chat with userId: %s and chatId: %s. Ex: %s",
            user_id,
            chatId,
            ex,
        )
        logging.error(error)
        return {"error": error}, 500

    return {"deleted_chatId": chatId}, 201


@chat.route("/send-message", methods=["POST"])
def send_message():
    db = get_database()
    payload = request.get_json()

    if not payload:
        return {"error": "Payload is missing."}, 400

    if "chatId" not in payload:
        return {"error": "Missing required field: 'chatId'."}, 400

    if "timestamp" not in payload:
        return {"error": "Missing required field: 'timestamp'."}, 400

    payload["chatId"] = ObjectId(payload["chatId"])
    payload["userId"] = session["userId"]
    payload["timestamp"] = datetime.now(tz=timezone.utc)

    user_msg = UserMessage.model_validate(payload)

    try:
        result = db.chats.update_one(
            {"_id": user_msg.chatId, "userId": user_msg.userId},
            {"$push": {"userMessages": user_msg.model_dump()}},
        )
        if result.matched_count == 0:
            error = (
                "No chat found matching chatId and/or userId: %s",
                str(user_msg.chatId),
            )
            logging.error(error)
            return {"error": error}, 404
    except Exception as ex:
        logging.error("Failed to upload user message to the database: %s", ex)
        return {"error": f"Failed to upload user message to the database: {ex}"}, 500

    # Generate AI response
    try:
        user_id = str(session.get("userId"))
        if not user_id:
            return {"error": "User not authenticated"}, 401
        
        # Retrieve previous messages from the chat for context
        chat_doc = db.chats.find_one(
            {"_id": user_msg.chatId, "userId": user_msg.userId}
        )
        
        previous_user_messages = []
        previous_model_messages = []
        conversation_history = []
        
        if chat_doc:
            # Get previous messages (excluding the one we just added)
            previous_user_messages = chat_doc.get("userMessages", [])
            previous_model_messages = chat_doc.get("modelMessages", [])
            
            # Remove the last user message if it's the one we just added
            # (it will have the same timestamp or be the most recent)
            if previous_user_messages and len(previous_user_messages) > 0:
                # The last message should be the one we just added, so take all but the last
                previous_user_messages = previous_user_messages[:-1]
            
            # Build conversation history for OpenAI
            if previous_user_messages or previous_model_messages:
                conversation_history = build_conversation_history(
                    user_messages=previous_user_messages,
                    model_messages=previous_model_messages,
                    max_messages=10
                )
        
        # Build prompts with conversation context
        system_prompt, context_message = build_chat_prompt(
            user_id=user_id,
            user_query=user_msg.message,
            previous_user_messages=previous_user_messages,
            previous_model_messages=previous_model_messages
        )
        
        # Generate response from OpenAI with conversation history
        ai_response = generate_chat_response(
            system_prompt=system_prompt,
            context_message=context_message,
            conversation_history=conversation_history if conversation_history else None
        )
        
        model_msg = ModelMessage.model_validate(payload)
        model_msg.message = ai_response
        
    except Exception as ex:
        logging.exception("Failed to generate AI response: %s", ex)  # Use exception() to get full traceback
        # Fallback to error message
        model_msg = ModelMessage.model_validate(payload)
        model_msg.message = "I apologize, but I'm having trouble processing your request right now. Please try again later."
    
    # Save model message to database
    try:
        db.chats.update_one(
            {"_id": model_msg.chatId, "userId": user_msg.userId},
            {"$push": {"modelMessages": model_msg.model_dump()}},
        )
    except Exception as ex:
        logging.error("Failed to upload model message to the database: %s", ex)
        return {"error": f"Failed to upload model message to the database: {ex}"}, 500

    return {"model_message": model_msg.message}, 201
