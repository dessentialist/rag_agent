import json
import logging
import uuid

from flask import Blueprint, jsonify, request

from database import db
from models import Conversation
from services.agent_registry import select_agent_for_request
from services.agno_service import generate_response
from services.pinecone_service import semantic_search
from services.settings_service import readiness

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py, just log a debug message to indicate this module is loaded
logger.debug("Chat routes logger configured with console output")

# Create a Blueprint for chat routes
chat_bp = Blueprint("chat_bp", __name__, url_prefix="/api")


# Agent selection is now done only when submitting a query


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Handle chat messages from the user and generate responses using Agno agent
    """
    try:
        # Get the message from the request
        data = request.json
        user_message = data.get("message", "")
        conversation_id = data.get("conversation_id")

        # Log the incoming message
        logger.info(f"Received chat message: '{user_message}'")
        logger.info(f"Conversation ID: {conversation_id or 'New conversation'}")

        # Validate the message
        if not user_message:
            logger.warning("Empty message received")
            return jsonify({"error": "Message is required"}), 400

        # Get or create a conversation
        conversation = None
        if conversation_id:
            conversation = db.session.get(Conversation, conversation_id)

            if not conversation:
                conversation_id = str(uuid.uuid4())
                conversation = Conversation(id=conversation_id)
                db.session.add(conversation)
                db.session.commit()

        # Add the user message to the conversation
        conversation.add_message(role="user", content=user_message)
        db.session.commit()

        # If app isn't ready, short-circuit with a clear error
        ready_state = readiness()
        if not ready_state.get("ready", False):
            logger.warning(f"Chat blocked; missing settings: {ready_state.get('missing_keys')}")
            return (
                jsonify(
                    {
                        "error": "App is not configured. Please complete settings.",
                        "missing_keys": ready_state.get("missing_keys", []),
                    }
                ),
                503,
            )

        # First, search for relevant documents to determine the agent to use
        logger.info("Searching for relevant documents to determine the appropriate agent")
        relevant_docs = semantic_search(user_message, limit=5)

        # Log basic information about the search results
        logger.info(f"Retrieved {len(relevant_docs)} documents for agent selection")

        # Select the agent via registry
        agent, rules = select_agent_for_request(relevant_docs, user_message)
        if not agent:
            return (
                jsonify({"error": "No agent matched selection rules. Define a default rule."}),
                400,
            )
        agno_response = generate_response(agent, user_message, relevant_docs)
        logger.debug(f"Raw response: {json.dumps(agno_response, indent=2)}")

        # Extract main content and resources from the Agno response
        if isinstance(agno_response, dict):
            ai_response = agno_response.get(
                "main", "I apologize, I could not generate a proper response."
            )

            next_steps = agno_response.get("next_steps", [])

        else:
            ai_response = "I apologize, I could not generate a proper response."
            next_steps = []

        # Add the AI response to the conversation
        conversation.add_message(role="assistant", content=ai_response)
        db.session.commit()

        # Log the AI response
        # Log truncated AI response for readability
        if ai_response and len(ai_response) > 150:
            logger.info(f"AI response (truncated): {ai_response[:150]}...")
        else:
            logger.info(f"AI response: {ai_response}")

        logger.info(f"Number of next steps: {len(next_steps) if next_steps else 0}")
        logger.info(f"Response saved to conversation: {conversation_id}")

        # Return the response and conversation ID (UI simplified, no resources)
        return jsonify(
            {
                "response": ai_response,
                "conversation_id": conversation_id,
                "next_steps": next_steps,
                "agent_type": getattr(agent, "name", None),
            }
        )

    except Exception as e:
        # Make sure to rollback any failed database operations
        db.session.rollback()
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your message"}), 500


@chat_bp.route("/conversations", methods=["GET"])
def get_conversations():
    """
    Get a list of all conversations
    """
    try:
        conversations = Conversation.query.all()
        conversation_list = []
        for conv in conversations:
            conversation_list.append(
                {
                    "id": conv.id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages),
                }
            )

        return jsonify({"conversations": conversation_list})

    except Exception as e:
        # Log the error with detailed information
        logger.error(f"Error in get_conversations endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving conversations"}), 500


@chat_bp.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    """
    Get a specific conversation by ID
    """
    try:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        return jsonify(
            {
                "conversation": {
                    "id": conversation.id,
                    "messages": [msg.to_dict() for msg in conversation.messages],
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                }
            }
        )

    except Exception as e:
        # Log the error with detailed information for troubleshooting
        logger.error(f"Error in get_conversation endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving the conversation"}), 500


@chat_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """
    Delete a specific conversation
    """
    try:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404

        db.session.delete(conversation)
        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_conversation endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while deleting the conversation"}), 500
