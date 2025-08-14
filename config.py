import os
import json

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

# Logging levels
LOG_LEVEL = "DEBUG"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================================
# FLASK AND DATABASE CONFIGURATION
# ============================================================

# Flask settings
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret")
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
DEBUG_MODE = True

# Database settings
# Default to a local SQLite file unless DATABASE_URL is provided
DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(os.getcwd(), 'rag_agent.db')}"
DATABASE_POOL_RECYCLE = 300
DATABASE_POOL_PRE_PING = True
DATABASE_TRACK_MODIFICATIONS = False

# ============================================================
# API KEYS AND EXTERNAL SERVICE CONFIGURATIONS
# ============================================================

# NOTE: Runtime OpenAI and embedding parameters are loaded from settings_service,
# not from this file. Values below are kept only as legacy placeholders.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 2000
LLM_RESPONSE_FORMAT = {"type": "json_object"}

# NOTE: Runtime Pinecone parameters are loaded from settings_service.
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "gcp-starter")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-agent-index")
PINECONE_DIMENSION = 1536
PINECONE_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-west-2"
PINECONE_SEARCH_LIMIT = 5

# ============================================================
# FILE UPLOAD AND PROCESSING CONFIGURATIONS
# ============================================================

# File upload constraints
ALLOWED_EXTENSIONS = {'txt', 'json', 'md', 'jsonl', 'csv'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size

# Knowledge base directory - where files are stored on disk
KNOWLEDGE_BASE_DIR = os.path.join(os.getcwd(), 'knowledge-base')

# Text chunking for RAG processing
CHUNK_SIZE = 500  # Size of document chunks in characters
CHUNK_OVERLAP = 30  # Overlap between chunks in characters

# ============================================================
# AI AGENT CONFIGURATIONS
# ============================================================

# Legacy agent constants are deprecated; agents are stored in DB and loaded via settings/registry.
COURSE_AGENT_NAME = "course-agent"
COURSE_AGENT_DESCRIPTION = "Course-focused agent"
COURSE_AGENT_INSTRUCTIONS = "Return response in JSON with keys 'main' and 'next_steps'."
DOC_AGENT_NAME = "doc-agent"
DOC_AGENT_DESCRIPTION = "Documentation-focused agent"
DOC_AGENT_INSTRUCTIONS = "Return response in JSON with keys 'main' and 'next_steps'."

# Shared Agent Persona (How the agent views itself)
AGENT_PERSONA = """You are a RAG-based knowledge retrieval system that EXCLUSIVELY uses information from retrieved documents to answer questions about BigID. Infer the purpose of the conversation. Answer in a format that would best be appropriate for the purpose of the conversation. Understand the nuances of why I might be giving those instructions to aid in answering in the most optimal manner.

Your purpose is to:
1. Search the knowledge base for relevant information
2. Use ONLY the information from retrieved documents to formulate responses
3. Clearly indicate when information is not available in the retrieved documents
4. NEVER use general knowledge or prior understanding about BigID

Provide precise citations and sources for every piece of information in your response, including links to documents. Format your answers clearly and concisely. Do not introduce any information that is not explicitly present in the retrieved documents.
"""

# Shared Agent Goal (Primary objective of the agent)
AGENT_GOAL = """The goal of this task is to provide STRICTLY RAG-based responses using ONLY information found in the retrieved documents. This is a RAG-only system where limiting responses to information available in the knowledge base is the PRIMARY objective, more important than providing a complete answer.

When users ask questions, the system should:
1. Use ONLY information found in the retrieved documents
2. NEVER use general knowledge or prior information about BigID
3. Clearly state when information is not available in the retrieved documents
4. Provide specific citations to document sources for all information
5. Shorten your answers to one or two sentences maximum, unless the user asks for more details

Users rely on this system to get accurate information strictly from the approved knowledge base, not to generate plausible or general responses based on the model's training."""

# RAG System Message Template (Shared)
RAG_SYSTEM_MESSAGE_TEMPLATE = """
# STRICT RAG-ONLY SYSTEM

You are a RAG-only knowledge retrieval system that can ONLY use information from the retrieved documents below.
You must NOT use any prior knowledge or general information about BigID.
You must NEVER generate information that isn't explicitly stated in the retrieved documents.

{instructions}

## RAG-ONLY GUIDELINES

1. If the documents contain relevant information, use ONLY that information in your response.
2. If the documents don't contain relevant information to answer the question, respond with: "I'm sorry, I couldn't find information about that in my knowledge base."
3. NEVER use any information beyond what is in the retrieved documents, even if you know the answer.
4. Cite your sources by mentioning which Document number (e.g., Document 1) you used for each piece of information.
5. Do not hallucinate links, facts, or information not present in the documents.
6. If you're unsure about something, say so clearly rather than guessing.

{persona}

{goal}
"""

# No Documents Message (Shared)
NO_DOCUMENTS_MESSAGE = "NO DOCUMENTS WERE FOUND IN THE KNOWLEDGE BASE. You must respond with: 'I'm sorry, I couldn't find information about that in my knowledge base.'"

# Critical Reminder Message (Shared)
CRITICAL_REMINDER_MESSAGE = "CRITICAL REMINDER: You must ONLY use information from the retrieved documents above. If the information isn't in the documents, say you don't have that information."

# Agent Tool Configuration (Shared)
AGENT_TOOLS = [{
    "name": "search_bigid_docs",
    "description": "Search BigID documentation",
    "parameters": {
        "query": {
            "type": "string",
            "description": "The search query"
        }
    }
}]



# ============================================================
# UI CONFIGURATIONS
# ============================================================

# Default course thumbnail
DEFAULT_COURSE_THUMBNAIL = "/static/images/course_thumbnail.svg"

# Chat UI Messages
BOT_WELCOME_MESSAGE = "Welcome! I'm your local RAG assistant. How can I help today?"

# Predefined prompts that appear after the welcome message
PREDEFINED_PROMPTS = [{
    "title": "What can you do?",
    "description": "What types of questions can I ask?"
}, {
    "title": "Search docs",
    "description": "Find info about data sources"
}, {
    "title": "Troubleshoot",
    "description": "Why isn't my index returning results?"
}]

# Convert PREDEFINED_PROMPTS to a JSON string for JavaScript consumption
PREDEFINED_PROMPTS_JSON = json.dumps(PREDEFINED_PROMPTS)

# UI Theme Configuration
THEME_COLORS = {
    "primary": "#7aa2f7",
    "secondary": "#6c757d",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "light": "#f8f9fa",
    "dark": "#343a40",
    "text-dark": "#212529",
    "text-light": "#f8f9fa",
    "text-muted": "#6c757d",
    "border": "#dee2e6"
}
