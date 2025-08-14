import os
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, EMBEDDING_MODEL

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the OpenAI client for embeddings
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_embeddings(text):
    """
    Generate embeddings for a text using OpenAI's embedding model
    
    Args:
        text: The text to generate embeddings for
    
    Returns:
        List of embedding values
    """
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    
    except Exception as e:
        logger.error(f"Error in generate_embeddings: {str(e)}", exc_info=True)
        raise