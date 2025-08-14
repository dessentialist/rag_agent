import logging

from services.settings_service import get_rag_settings

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py
# Just initialize logger for this module


def chunk_text(text, chunk_size=None, chunk_overlap=None):
    """
    Split text into chunks of specified size with overlap

    Args:
        text: Text to split
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters

    Returns:
        List of text chunks
    """
    try:
        # Handle empty or None text
        if not text:
            return []

        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)

        # Load chunking settings if not provided
        if chunk_size is None or chunk_overlap is None:
            rag_cfg = get_rag_settings()
            if chunk_size is None:
                chunk_size = int(rag_cfg.get("chunk_size", 500))
            if chunk_overlap is None:
                chunk_overlap = int(rag_cfg.get("chunk_overlap", 30))

        chunks = []
        text_length = len(text)

        # Handle short text that doesn't need chunking
        if text_length <= chunk_size:
            return [text]

        # Split text into paragraphs first for more natural chunking
        paragraphs = text.split("\n")
        current_chunk = ""

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) + 1 > chunk_size:
                # If current_chunk is not empty, add it to chunks
                if current_chunk:
                    chunks.append(current_chunk)

                # Start a new chunk with overlap
                if chunks:
                    # Find the last few sentences or paragraphs to include as overlap
                    overlap_text = (
                        chunks[-1][-chunk_overlap:]
                        if len(chunks[-1]) > chunk_overlap
                        else chunks[-1]
                    )
                    current_chunk = overlap_text + "\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    except Exception as e:
        logger.error(f"Error in chunk_text: {str(e)}", exc_info=True)
        # Return the original text as a single chunk in case of error
        return [text] if text else []


def chunk_document(doc_id, content, metadata=None):
    """
    Chunk a document and prepare it for vector storage

    Args:
        doc_id: Document ID
        content: Document content
        metadata: Document metadata

    Returns:
        List of (chunk_id, chunk_text, chunk_metadata) tuples
    """
    try:
        chunks = chunk_text(content)
        result = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"

            # Create metadata for this chunk
            chunk_metadata = {
                "content": chunk,
                "doc_id": doc_id,
                "chunk_index": i,
                "chunk_count": len(chunks),
            }

            # Add the original metadata
            if metadata:
                for key, value in metadata.items():
                    if key != "content":  # Avoid overwriting content
                        chunk_metadata[key] = value

            result.append((chunk_id, chunk, chunk_metadata))

        return result

    except Exception as e:
        logger.error(f"Error in chunk_document: {str(e)}", exc_info=True)
        return []
