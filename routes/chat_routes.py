import logging
import json
import uuid
import asyncio
from flask import Blueprint, request, jsonify
from services.agno_service import select_agent_by_doc_type, doc_agent, course_agent
from services.pinecone_service import semantic_search
from models import Message, Conversation
from database import db
from config import LOG_LEVEL, LOG_FORMAT

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py, just log a debug message to indicate this module is loaded
logger.debug("Chat routes logger configured with console output")

# Create a Blueprint for chat routes
chat_bp = Blueprint('chat_bp', __name__, url_prefix='/api')


# Agent selection is now done only when submitting a query


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat messages from the user and generate responses using Agno agent
    """
    try:
        # Get the message from the request
        data = request.json
        user_message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        # Log the incoming message
        logger.info(f"Received chat message: '{user_message}'")
        logger.info(f"Conversation ID: {conversation_id or 'New conversation'}")

        # Validate the message
        if not user_message:
            logger.warning("Empty message received")
            return jsonify({'error': 'Message is required'}), 400

        # Get or create a conversation
        conversation = None
        if conversation_id:
            conversation = Conversation.query.get(conversation_id)

        if not conversation:
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(id=conversation_id)
            db.session.add(conversation)
            db.session.commit()

        # Add the user message to the conversation
        conversation.add_message(role="user", content=user_message)
        db.session.commit()

        # Create an event loop for async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # First, search for relevant documents to determine the agent to use
        logger.info("Searching for relevant documents to determine the appropriate agent")
        relevant_docs = semantic_search(user_message, limit=5)
        
        # Log basic information about the search results
        logger.info(f"Retrieved {len(relevant_docs)} documents for agent selection")
        
        # Select the appropriate agent based solely on document Type value
        selected_agent = select_agent_by_doc_type(relevant_docs)
        
        # Set agent_type string based on the selected agent
        if selected_agent == doc_agent:
            agent_type = "documentation"
            logger.info("Selected documentation agent based on document Type value")
        else:
            agent_type = "course"
            logger.info("Selected course agent (default if no documentation Type found)")
        
        # Generate a response using the selected Agno agent
        # Pass the pre-retrieved documents to avoid duplicate search
        logger.info(f"Generating response with selected agent for: {user_message}")
        context = {'relevant_docs': relevant_docs, 'agent_type': agent_type}
        agno_response = loop.run_until_complete(
            selected_agent.run(user_message, context=context))
        logger.debug(f"Raw Agno response: {json.dumps(agno_response, indent=2)}")

        # Extract main content and resources from the Agno response
        if isinstance(agno_response, dict):
            ai_response = agno_response.get(
                'main', 'I apologize, I could not generate a proper response.')

            # Extract resources - simplified to just get a URL string for course agent
            resources = None
            resource_links = agno_response.get('resources', [])
            
            # For course agent, extract the first URL as a simple string
            if agent_type == "course" and resource_links:
                # Simplify resource handling to just extract a single URL for course agent
                if isinstance(resource_links, list) and len(resource_links) > 0:
                    # Get the first resource URL
                    if isinstance(resource_links[0], dict) and 'url' in resource_links[0]:
                        resources = resource_links[0]['url']
                    elif isinstance(resource_links[0], str):
                        resources = resource_links[0]
                elif isinstance(resource_links, str):
                    # If it's just a URL string
                    resources = resource_links
            
            # Extract next steps
            next_steps = agno_response.get('next_steps', [])

        else:
            ai_response = "I apologize, I could not generate a proper response."
            resources = []
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
        
        # Safely log resource information
        if resources:
            if isinstance(resources, list):
                logger.info(f"Number of resources: {len(resources)}")
            else:
                logger.info(f"Resource URL: {resources}")
        else:
            logger.info("No resources included in the response")
            
        logger.info(f"Number of next steps: {len(next_steps) if next_steps else 0}")
        logger.info(f"Response saved to conversation: {conversation_id}")

        # Return the response and conversation ID, including the agent type that was used
        return jsonify({
            'response': ai_response,
            'conversation_id': conversation_id,
            'resources': resources,
            'next_steps': next_steps,
            'agent_type': agent_type
        })

    except Exception as e:
        # Make sure to rollback any failed database operations
        db.session.rollback()
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify(
            {'error': 'An error occurred while processing your message'}), 500


@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """
    Get a list of all conversations
    """
    try:
        conversations = Conversation.query.all()
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                'id': conv.id,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': len(conv.messages)
            })

        return jsonify({'conversations': conversation_list})

    except Exception as e:
        # Log the error with detailed information
        logger.error(f"Error in get_conversations endpoint: {str(e)}",
                     exc_info=True)
        return jsonify(
            {'error': 'An error occurred while retrieving conversations'}), 500


@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """
    Get a specific conversation by ID
    """
    try:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404

        return jsonify({
            'conversation': {
                'id': conversation.id,
                'messages': [msg.to_dict() for msg in conversation.messages],
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            }
        })

    except Exception as e:
        # Log the error with detailed information for troubleshooting
        logger.error(f"Error in get_conversation endpoint: {str(e)}",
                     exc_info=True)
        return jsonify(
            {'error':
             'An error occurred while retrieving the conversation'}), 500


@chat_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """
    Delete a specific conversation
    """
    try:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404

        db.session.delete(conversation)
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in delete_conversation endpoint: {str(e)}",
                     exc_info=True)
        return jsonify(
            {'error':
             'An error occurred while deleting the conversation'}), 500
