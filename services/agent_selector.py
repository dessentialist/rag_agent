import logging
from typing import Any, Dict, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AgentSelector:
    """
    A robust component for selecting the appropriate agent based on document metadata.

    This class encapsulates the logic for determining which agent to use based on
    document types, content patterns, and user query characteristics.
    """

    # Document type constants for consistent comparison
    DOC_TYPE_DOCUMENTATION = "documentation"
    DOC_TYPE_COURSE = "course"
    DOC_TYPE_UNKNOWN = "unknown"

    def __init__(self, doc_agent=None, course_agent=None):
        """
        Initialize the AgentSelector with available agents

        Args:
            doc_agent: The agent specialized for documentation
            course_agent: The agent specialized for courses
        """
        self.doc_agent = doc_agent
        self.course_agent = course_agent
        logger.info("Initialized AgentSelector component")

    def select_agent(self, relevant_docs: List[Dict]) -> Tuple[Any, str]:
        """
        Select the appropriate agent based solely on document Type value

        Args:
            relevant_docs: List of relevant documents from semantic search

        Returns:
            Tuple of (selected_agent, agent_type_string)
        """
        # Simply check each document for a "Type" value of "documentation"
        for doc in relevant_docs:
            # Extract the type value directly from metadata
            metadata = doc.get("metadata", {}) or {}
            doc_type = metadata.get("type", "")

            # Log the document type for debugging
            doc_id = doc.get("id", "unknown")
            logger.info(f"Document {doc_id} has type: {doc_type}")

            # Check if this document has type "documentation" (case-insensitive)
            if isinstance(doc_type, str) and doc_type.lower() == self.DOC_TYPE_DOCUMENTATION:
                logger.info(f"Selecting documentation agent based on document type: {doc_type}")
                return self.doc_agent, "documentation"

        # If no documentation type found, use course agent
        logger.info("Selecting course agent (no documentation type found)")
        return self.course_agent, "course"


# No longer needed as we're only using document types for selection
