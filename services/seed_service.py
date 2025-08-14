import logging
import uuid

from database import db
from models import Document
from services.agent_registry import ensure_default_agents
from services.file_service import process_file_for_rag, save_file

logger = logging.getLogger(__name__)


def ensure_sample_content() -> None:
    """
    Seed a minimal sample document and ensure default agents exist.

    This is safe to call multiple times: it checks for an existing
    sample by filename.
    """
    try:
        # Ensure agents are present (no-op if already there)
        ensure_default_agents()

        # Check for existing sample doc
        existing = Document.query.filter_by(filename="sample_documentation.txt").first()
        if existing:
            logger.info("Sample documentation already present; skipping seeding")
            return

        sample_text = (
            "RAG Agent Overview\n\n"
            "This is a documentation file for the RAG Agent demo.\n\n"
            "Key facts:\n"
            "- The retrieval pipeline includes: chunking, embedding, and vector search.\n"
            "- Pinecone is used as the vector database with cosine similarity.\n"
            "- OpenAI's text-embedding-3-small model generates 1536-dim embeddings.\n"
            "- Responses must only use retrieved document content.\n\n"
            "FAQ:\n"
            "Q: What vector database is used?\nA: Pinecone.\n\n"
            "Q: What are the major steps?\nA: Chunking, embedding, and vector search.\n"
        )

        file_id = str(uuid.uuid4())
        filename = "sample_documentation.txt"
        file_type = "txt"

        # Save and process file for RAG
        save_file(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            content=sample_text,
            detected_doc_type="documentation",
        )
        process_file_for_rag(file_id=file_id, filename=filename, content=sample_text, file_type=file_type)

        db.session.commit()
        logger.info("Seeded sample documentation and vectors")
    except Exception as exc:  # noqa: BLE001
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.warning(f"Seeding sample content failed: {exc}")


