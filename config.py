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
SESSION_SECRET = os.environ.get("SESSION_SECRET")
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
DEBUG_MODE = True

# Database settings
DATABASE_URI = os.environ.get("DATABASE_URL")
DATABASE_POOL_RECYCLE = 300
DATABASE_POOL_PRE_PING = True
DATABASE_TRACK_MODIFICATIONS = False

# ============================================================
# API KEYS AND EXTERNAL SERVICE CONFIGURATIONS
# ============================================================

# OpenAI API Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
LLM_TEMPERATURE = 0.3  # Lower temperature for more deterministic responses based on source material
LLM_MAX_TOKENS = 2000  # Maximum tokens for the AI response
LLM_RESPONSE_FORMAT = {
    "type": "json_object"
}  # Format for structured responses

# Pinecone Vector Database Configuration
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "gcp-starter")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "bigid-university")
PINECONE_DIMENSION = 1536  # Dimension for 'text-embedding-3-small'
PINECONE_METRIC = "cosine"  # Similarity metric
PINECONE_CLOUD = "aws"  # Cloud provider
PINECONE_REGION = "us-west-2"  # Region
PINECONE_SEARCH_LIMIT = 5  # Number of relevant documents to return in search

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

# Course Agent Configuration
COURSE_AGENT_NAME = "course-agent"
COURSE_AGENT_DESCRIPTION = "AI Tutor for BigID University Course Content"

# Course Agent Instructions (Controls response format and behavior)
COURSE_AGENT_INSTRUCTIONS = """Return response in JSON. Use the following keys - 'main','resources','next_steps'. 
- 'main': should contain the main body of the answer. 
- 'resources': should be only the course link, that is given in the RAG document context directly as the value for the key "URL". That will be rendered as a multimedia item in the front end.
- 'next_steps': should be a list of 2-3 suggested next steps related to the current question that the user might want to explore. It should be brief and concise. It should not contain any hyperlinks. Don't use more than 7-8 words in condensed sentences that are easy to understand.

IMPORTANT: ONLY USE INFORMATION FROM THE PROVIDED DOCUMENTS TO ANSWER QUESTIONS.
DO NOT use any prior knowledge or information not contained in the retrieved documents.
You have NO general knowledge about BigID outside of the specific documents retrieved for each query.
If the retrieved documents don't contain information relevant to the question, respond with: 'I'm sorry, I couldn't find information about that in my knowledge base.' DO NOT attempt to answer based on general knowledge.
INCLUDE hyperlinks and other citations to the source URL of the information you used in your response.
DON'T Answer questions that are not related to BigID.
Answer questions EXCLUSIVELY USING the retrieved documents provided. NEVER rely on any other knowledge.
NEVER MENTION COMPETITORS.
NEVER speculate or infer information not explicitly stated in the retrieved documents.

WRITING Style: 

1. **Simple and compelling language:** Keeps the content easy to understand and engaging.
2. **Concise and active voice:** Avoids lengthy explanations and uses direct, action-oriented sentences.
3. **Avoids clichés and obscure words:** Ensures originality and accessibility.
4. **Varied sentence lengths:** Maintains reader interest with dynamic pacing.
5. **Business writing proficiency:** Excels in presenting complex or technical topics clearly and straightforwardly.
"""

# Documentation Agent Configuration
DOC_AGENT_NAME = "doc-agent"
DOC_AGENT_DESCRIPTION = "AI Tutor for BigID Technical Documentation"

# Documentation Agent Instructions (Controls response format and behavior)
DOC_AGENT_INSTRUCTIONS = """Return response in JSON. Use the following keys - 'main','next_steps'. 
- 'main': should contain the main body of the answer. 
- 'next_steps': should be a list of 2-3 suggested next steps related to the current question that the user might want to explore. It should be brief and concise. It should not contain any hyperlinks. Don't use more than 7-8 words in condensed sentences that are easy to understand.
IMPORTANT: ONLY USE INFORMATION FROM THE PROVIDED DOCUMENTS TO ANSWER QUESTIONS.
DO NOT use any prior knowledge or information not contained in the retrieved documents.
You have NO general knowledge about BigID outside of the specific documents retrieved for each query.
If the retrieved documents don't contain information relevant to the question, respond with: 'I'm sorry, I couldn't find information about that in my knowledge base.' DO NOT attempt to answer based on general knowledge.
INCLUDE hyperlinks and other citations to the source URL of the information you used in your response.
DON'T Answer questions that are not related to BigID.
Answer questions EXCLUSIVELY USING the retrieved documents provided. NEVER rely on any other knowledge.
NEVER MENTION COMPETITORS.
NEVER speculate or infer information not explicitly stated in the retrieved documents.

WRITING Style: 

1. **Simple and compelling language:** Keeps the content easy to understand and engaging.
2. **Concise and active voice:** Avoids lengthy explanations and uses direct, action-oriented sentences.
3. **Avoids clichés and obscure words:** Ensures originality and accessibility.
4. **Varied sentence lengths:** Maintains reader interest with dynamic pacing.
5. **Business writing proficiency:** Excels in presenting complex or technical topics clearly and straightforwardly.
"""

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
BOT_WELCOME_MESSAGE = "Hey there! I'm your AI assistant for all things BigID. What can I do for you today?"

# Predefined prompts that appear after the welcome message
PREDEFINED_PROMPTS = [{
    "title": "My First Course",
    "description": "Help me enroll in my first course."
}, {
    "title": "What Can I Learn Here",
    "description": "Guide me through the BigID catalog."
}, {
    "title": "Training Credits",
    "description": "What are they, and how to use them?"
}]

# Convert PREDEFINED_PROMPTS to a JSON string for JavaScript consumption
PREDEFINED_PROMPTS_JSON = json.dumps(PREDEFINED_PROMPTS)

# UI Theme Configuration
THEME_COLORS = {
    "primary": "#a153e4",  # BigID Purple
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
