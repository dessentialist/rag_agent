import logging
from typing import List
from openai import OpenAI
from services.settings_service import get_openai_settings, get_embedding_settings, SettingsValidationError

# Configure logging
logger = logging.getLogger(__name__)

def _get_client() -> OpenAI:
    """Create an OpenAI client using API key from settings.

    Raises a SettingsValidationError if the API key is missing, so callers can
    surface a clear configuration error rather than a runtime crash.
    """
    cfg = get_openai_settings()
    api_key = cfg.get("api_key")
    if not api_key:
        raise SettingsValidationError("OpenAI API key is not configured. Please set it in settings.")
    return OpenAI(api_key=api_key)

def generate_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for a text using OpenAI's embedding model
    
    Args:
        text: The text to generate embeddings for
    
    Returns:
        List of embedding values
    """
    try:
        embed_cfg = get_embedding_settings()
        embedding_model = embed_cfg.get("embedding_model")
        if not embedding_model:
            raise SettingsValidationError("Embedding model is not configured. Please set it in settings.")

        response = _get_client().embeddings.create(
            model=embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    except Exception as e:
        logger.error(f"Error in generate_embeddings: {str(e)}", exc_info=True)
        raise