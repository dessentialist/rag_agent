import os
import logging
import uuid
from pinecone import Pinecone, ServerlessSpec
from config import (
    PINECONE_API_KEY, 
    PINECONE_ENVIRONMENT, 
    PINECONE_INDEX_NAME,
    PINECONE_DIMENSION,
    PINECONE_METRIC,
    PINECONE_CLOUD,
    PINECONE_REGION,
    PINECONE_SEARCH_LIMIT,
    LOG_LEVEL,
    LOG_FORMAT
)
from services.embeddings_service import generate_embeddings

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py
logger.debug("Pinecone service logger configured with console output")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create the index if it doesn't exist
def initialize_pinecone():
    """
    Initialize Pinecone and create the index if it doesn't exist
    """
    try:
        # Check if the index exists
        all_indexes = pc.list_indexes()
        if PINECONE_INDEX_NAME not in [idx.name for idx in all_indexes]:
            logger.info(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
            
            # Create the index
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=PINECONE_DIMENSION,
                metric=PINECONE_METRIC,
                spec=ServerlessSpec(
                    cloud=PINECONE_CLOUD,
                    region=PINECONE_REGION
                )
            )
            logger.info(f"Pinecone index {PINECONE_INDEX_NAME} created successfully")
        else:
            logger.info(f"Pinecone index {PINECONE_INDEX_NAME} already exists")
    
    except Exception as e:
        logger.error(f"Error initializing Pinecone: {str(e)}", exc_info=True)
        raise

# Initialize Pinecone on module import
try:
    initialize_pinecone()
    # Connect to the index
    index = pc.Index(PINECONE_INDEX_NAME)
    logger.info(f"Connected to Pinecone index: {PINECONE_INDEX_NAME}")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}", exc_info=True)
    index = None

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
        index.upsert(
            vectors=[
                {
                    "id": id,
                    "values": embedding,
                    "metadata": metadata or {}
                }
            ]
        )
        
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
        if index is None:
            logger.error("[LIST] Pinecone index is not initialized")
            return {"stats": {"total_chunks": 0, "unique_files": 0}, "documents": []}
        
        # Initialize empty list to store vectors
        all_documents = []
        
        # Use query with a dummy vector to get vectors from the index
        response = index.query(
            vector=[0.0] * PINECONE_DIMENSION,  # Dummy vector with floats
            top_k=1000,                        # Return up to 1000 results
            include_metadata=True
        )
        
        if not hasattr(response, 'matches') or not response.matches:
            logger.info("[LIST] No vectors found in Pinecone")
            return {"stats": {"total_chunks": 0, "unique_files": 0}, "documents": []}
        
        # Track unique document IDs
        unique_files = set()
        for match in response.matches:
            if hasattr(match, 'metadata') and match.metadata and 'source_file_id' in match.metadata:
                source_id = match.metadata.get('source_file_id')
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
                    all_documents.append({
                        "file_id": source_id,
                        "filename": match.metadata.get("source_filename", "Unknown"),
                        "chunks": 1,
                        "vector_id": match.id,
                        "title": match.metadata.get("title", "Unknown")
                    })
        
        # Sort documents by filename
        all_documents.sort(key=lambda x: x.get("filename", "").lower())
        
        # Construct the result
        result = {
            "stats": {
                "total_chunks": len(response.matches),
                "unique_files": len(unique_files)
            },
            "documents": all_documents
        }
        
        logger.info(f"[LIST] Found {result['stats']['total_chunks']} chunks from {result['stats']['unique_files']} unique files")
        return result
    
    except Exception as e:
        logger.error(f"[LIST] Error listing vectors from Pinecone: {str(e)}", exc_info=True)
        return {"stats": {"total_chunks": 0, "unique_files": 0}, "documents": []}

def semantic_search(query, limit=PINECONE_SEARCH_LIMIT):
    """
    Perform semantic search using Pinecone
    
    Args:
        query: The query text
        limit: Maximum number of results to return (defaults to PINECONE_SEARCH_LIMIT from config)
    
    Returns:
        List of documents with content and metadata
    """
    try:
        if index is None:
            logger.error("[SEARCH] Pinecone index is not initialized")
            return []
        
        # Log search query
        logger.info(f"[SEARCH] Performing semantic search for query: '{query}'")
        logger.info(f"[SEARCH] Requested {limit} results")
        
        # Generate embeddings for the query
        query_embedding = generate_embeddings(query)
        logger.info(f"[SEARCH] Generated query embedding vector of dimension {len(query_embedding)}")
        
        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True
        )
        
        # Log search results summary
        if hasattr(results, 'matches') and results.matches:
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
                "metadata": {k: v for k, v in match.metadata.items() if k != "content"}
            }
            documents.append(doc)
        
        return documents
    
    except Exception as e:
        logger.error(f"[SEARCH] Error in semantic search: {str(e)}", exc_info=True)
        return []
