import logging
from typing import Optional

from pinecone import Pinecone, ServerlessSpec

from services.embeddings_service import generate_embeddings
from services.settings_service import SettingsValidationError, get_pinecone_settings

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py
logger.debug("Pinecone service logger configured with console output")

_pc: Optional[Pinecone] = None
_index = None


# Create the index if it doesn't exist
def _get_pinecone_client() -> Pinecone:
    cfg = get_pinecone_settings()
    api_key = cfg.get("api_key")
    if not api_key:
        raise SettingsValidationError(
            "Pinecone API key is not configured. Please set it in settings."
        )
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=api_key)
    return _pc


def initialize_pinecone():
    """
    Initialize Pinecone and create the index if it doesn't exist
    """
    try:
        cfg = get_pinecone_settings()
        index_name = cfg.get("index_name")
        dimension = cfg.get("dimension")
        metric = cfg.get("metric", "cosine")
        cloud = cfg.get("cloud", "aws")
        region = cfg.get("region", "us-west-2")
        if not index_name or not dimension:
            raise SettingsValidationError(
                "Pinecone index_name and dimension are required in settings."
            )

        pc = _get_pinecone_client()
        all_indexes = pc.list_indexes()
        if index_name not in [idx.name for idx in all_indexes]:
            logger.info(f"Creating Pinecone index: {index_name}")

            # Create the index
            pc.create_index(
                name=index_name,
                dimension=int(dimension),
                metric=metric,
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
            logger.info(f"Pinecone index {index_name} created successfully")
        else:
            logger.info(f"Pinecone index {index_name} already exists")

    except Exception as e:
        logger.error(f"Error initializing Pinecone: {str(e)}", exc_info=True)
        raise


def _get_index():
    global _index
    if _index is not None:
        return _index
    cfg = get_pinecone_settings()
    index_name = cfg.get("index_name")
    if not index_name:
        raise SettingsValidationError("Pinecone index_name is not configured.")
    pc = _get_pinecone_client()
    try:
        initialize_pinecone()
        _index = pc.Index(index_name)
        logger.info(f"Connected to Pinecone index: {index_name}")
        return _index
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {str(e)}", exc_info=True)
        return None


# Note: connectivity is checked in settings_service.diagnostics_connectivity to avoid circular imports.


def upsert_to_pinecone(id, content, metadata=None):
    """
    Generate embeddings for content and upsert to Pinecone

    Args:
        id: Unique identifier for the vector
        content: Text content to generate embeddings for
        metadata: Optional metadata to store with the vector

    Returns:
        Boolean indicating success
    """
    try:
        index = _get_index()
        if index is None:
            logger.error("[EMBEDDING] Pinecone index is not initialized")
            return False

        # Log content information
        content_preview = content[:100] + "..." if len(content) > 100 else content
        logger.info(f"[EMBEDDING] Generating embeddings for content: {content_preview}")
        logger.info(f"[EMBEDDING] Content length: {len(content)} characters, ID: {id}")

        # Generate embeddings
        embedding = generate_embeddings(content)
        logger.info(f"[EMBEDDING] Generated embedding vector of dimension {len(embedding)}")

        # Extract metadata info for logging
        source_file = metadata.get("source_filename", "unknown") if metadata else "unknown"
        chunk_index = metadata.get("chunk_index", "N/A") if metadata else "N/A"
        total_chunks = metadata.get("total_chunks", "N/A") if metadata else "N/A"

        # Upsert to Pinecone
        index.upsert(vectors=[{"id": id, "values": embedding, "metadata": metadata or {}}])

        logger.info(f"[EMBEDDING] Successfully upserted document with ID: {id}")
        logger.info(f"[EMBEDDING] Source: {source_file}, Chunk: {chunk_index}/{total_chunks}")
        return True

    except Exception as e:
        logger.error(f"[EMBEDDING] Error upserting to Pinecone: {str(e)}", exc_info=True)
        return False


def delete_from_pinecone(id):
    """
    Delete a vector from Pinecone by ID

    Args:
        id: ID of the vector to delete

    Returns:
        Boolean indicating success
    """
    try:
        index = _get_index()
        if index is None:
            logger.error("Pinecone index is not initialized")
            return False

        # Delete from Pinecone
        index.delete(ids=[id])

        logger.debug(f"Successfully deleted document with ID: {id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting from Pinecone: {str(e)}", exc_info=True)
        return False


def list_all_vectors():
    """
    List all vectors in Pinecone with their metadata

    Returns:
        Dictionary with document stats and list of unique documents
    """
    try:
        index = _get_index()
        if index is None:
            logger.error("[LIST] Pinecone index is not initialized")
            return {"stats": {"total_chunks": 0, "unique_files": 0}, "documents": []}

        # Initialize empty list to store vectors
        all_documents = []

        # Use query with a dummy vector to get vectors from the index
        cfg = get_pinecone_settings()
        dimension = int(cfg.get("dimension", 1536))
        response = index.query(
            vector=[0.0] * dimension,  # Dummy vector with floats
            top_k=1000,  # Return up to 1000 results
            include_metadata=True,
        )

        if not hasattr(response, "matches") or not response.matches:
            logger.info("[LIST] No vectors found in Pinecone")
            return {"stats": {"total_chunks": 0, "unique_files": 0}, "documents": []}

        # Track unique document IDs
        unique_files = set()
        for match in response.matches:
            if hasattr(match, "metadata") and match.metadata and "source_file_id" in match.metadata:
                source_id = match.metadata.get("source_file_id")
                unique_files.add(source_id)

                # Check if we've already added this document
                doc_exists = False
                for doc in all_documents:
                    if doc.get("file_id") == source_id:
                        doc_exists = True
                        # Update chunk count
                        doc["chunks"] += 1
                        break

                # If document doesn't exist in our list, add it
                if not doc_exists:
                    all_documents.append(
                        {
                            "file_id": source_id,
                            "filename": match.metadata.get("source_filename", "Unknown"),
                            "chunks": 1,
                            "vector_id": match.id,
                            "title": match.metadata.get("title", "Unknown"),
                        }
                    )

        # Sort documents by filename
        all_documents.sort(key=lambda x: x.get("filename", "").lower())

        # Construct the result
        result = {
            "stats": {"total_chunks": len(response.matches), "unique_files": len(unique_files)},
            "documents": all_documents,
        }

        logger.info(
            f"[LIST] Found {result['stats']['total_chunks']} chunks from {result['stats']['unique_files']} unique files"
        )
        return result

    except Exception as e:
        logger.error(f"[LIST] Error listing vectors from Pinecone: {str(e)}", exc_info=True)
        return {"stats": {"total_chunks": 0, "unique_files": 0}, "documents": []}


def semantic_search(query, limit=None):
    """
    Perform semantic search using Pinecone

    Args:
        query: The query text
        limit: Maximum number of results to return (defaults to PINECONE_SEARCH_LIMIT from config)

    Returns:
        List of documents with content and metadata
    """
    try:
        index = _get_index()
        if index is None:
            logger.error("[SEARCH] Pinecone index is not initialized")
            return []

        # Log search query
        logger.info(f"[SEARCH] Performing semantic search for query: '{query}'")
        if limit is None:
            cfg = get_pinecone_settings()
            limit = int(cfg.get("search_limit", 5))
        logger.info(f"[SEARCH] Requested {limit} results")

        # Generate embeddings for the query
        query_embedding = generate_embeddings(query)
        logger.info(
            f"[SEARCH] Generated query embedding vector of dimension {len(query_embedding)}"
        )

        # Search Pinecone
        results = index.query(vector=query_embedding, top_k=limit, include_metadata=True)

        # Log search results summary
        if hasattr(results, "matches") and results.matches:
            logger.info(f"[SEARCH] Found {len(results.matches)} matching documents")
            for i, match in enumerate(results.matches):
                score_percentage = round(match.score * 100, 2)
                logger.info(f"[SEARCH] Match {i+1}: ID={match.id}, Similarity={score_percentage}%")
        else:
            logger.warning(f"[SEARCH] No matching documents found for query: '{query}'")

        # Extract and return the results
        documents = []
        for match in results.matches:
            doc = {
                "id": match.id,
                "score": match.score,
                "content": match.metadata.get("content", ""),
                "metadata": {k: v for k, v in match.metadata.items() if k != "content"},
            }
            documents.append(doc)

        return documents

    except Exception as e:
        logger.error(f"[SEARCH] Error in semantic search: {str(e)}", exc_info=True)
        return []
