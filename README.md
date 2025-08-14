# RAG Agent – Local-first Configurable Chatbot

An open, neutral, local-first RAG chatbot with configurable settings, multi-agent registry, and SQLite by default. Designed to run on macOS easily with a Makefile and venv. No client branding.

![RAG Agent](generated-icon.png)

## Overview

This application is an AI-powered local assistant designed to help users query their own knowledge base, navigate content, and troubleshoot issues by providing accurate, relevant information from retrieved documents. The system uses a combination of technologies:

- **Retrieval-Augmented Generation (RAG)**: Enhances the AI's responses by retrieving relevant information from a knowledge base
- **Vector Database (Pinecone)**: Stores document embeddings for semantic search
- **OpenAI Integration**: Powers the AI's understanding and response generation
  

## Key Features

- **Intelligent Chatbot Interface**: 
  - Ask questions and receive accurate answers based on your uploaded knowledge base
  - Streamlined responses with main content and optional next steps
  - Real-time markdown rendering during typing animation for immediate text formatting
  - Simplified predefined prompts with prominent titles and centered text
  - Improved UI flow with intuitive component organization
- **Document Management**: Upload, view, and delete files (supports TXT, JSON, MD, JSONL, CSV, DOCX, PDF, XLSX)
- **Database Document Storage**: Files uploaded through the UI are saved directly to the local SQLite database by default (Postgres optional)
- **Vector Embedding Storage**: Document chunks are stored in Pinecone with their vector embeddings for semantic search
- **Semantic Search**: Uses vector embeddings to find the most relevant information for user queries
- **Comprehensive Logging**: Detailed logs for chat conversations, RAG retrieval, API calls, file operations, and vector operations
- **Centralized Configuration**: Runtime settings are managed via the Settings store (SQLite) and accessed through `services/settings_service.py`. Minimal legacy defaults remain in `config.py`.

## System Architecture

The application follows a modular architecture:

- **Frontend**: HTML/CSS/JavaScript interface with separate pages for chat and file management
- **Backend**: Flask-based Python server with RESTful API endpoints
- **Database**: SQLite by default with SQLAlchemy ORM (Postgres optional via `DATABASE_URL`)
- **Vector Storage**: Pinecone vector database for semantic search capabilities
- **File Storage**: Files stored in the database; Pinecone stores embeddings
- **Configuration**: Settings-driven runtime via `services/settings_service.py`; minimal legacy boot values in `config.py`

## Components

- **Chat Interface**: Ask questions and receive AI-powered responses
- **File Management**: Upload, view, and delete documents
- **Vector DB Stats**: View Pinecone document/chunk stats; refresh and manage
- **Agno Agent**: Integration layer for AI capabilities
- **Database Models**: Stores conversations, messages, documents, and document chunks
- **Configuration System**: Centralized settings in config.py organized by function

## Prerequisites

- Python 3.11+
- OpenAI API Key
- Pinecone API Key

## Environment Variables

Most configuration now lives in the Settings store (SQLite). Optionally set:

- `DATABASE_URL` (if using Postgres instead of default SQLite)
- `SESSION_SECRET` (otherwise a dev default is used)

## Setup and Installation

1. Clone the repository
2. Create venv and install: `make venv && make install`
3. Run the server: `make run`
4. Open `http://localhost:5000/` — on first run, you will be redirected to the Settings page to configure providers (OpenAI, Pinecone), defaults, theme, and agents. Diagnostics must pass (OpenAI and Pinecone connectivity) before chat/files are enabled.

## Directory Structure

```
.
├── app.py                  # Flask app configuration
├── config.py               # Configuration settings
├── database.py             # Database setup
├── main.py                 # Application entry point
├── models.py               # Database models
├── knowledge-base/         # Directory for synced files
├── routes/                 # API routes
│   ├── __init__.py
│   ├── chat_routes.py      # Chat endpoints
│   └── file_routes.py      # File management endpoints
├── services/               # Business logic
│   ├── __init__.py
│   ├── agno_service.py     # AI agent implementation
│   ├── embeddings_service.py # Vector embeddings
│   ├── file_service.py     # File operations
│   └── pinecone_service.py # Vector database operations
├── static/                 # Static assets
│   ├── css/
│   └── js/
├── templates/              # HTML templates
└── utils/                  # Utility functions
    ├── __init__.py
    └── embeddings.py       # Text chunking utilities
```

## API Endpoints

### Chat API

- `POST /api/chat`: Send a message to the AI and receive a response
- `GET /api/conversations`: Get a list of all conversations
- `GET /api/conversations/<id>`: Get a specific conversation
- `DELETE /api/conversations/<id>`: Delete a conversation

### File API

- `POST /api/files/upload`: Upload a file
- `GET /api/files`: Get a list of all files
- `GET /api/files/<id>`: Get a specific file
- `DELETE /api/files/<id>`: Delete a file
- `DELETE /api/files`: Delete all files
- `GET/POST /api/files/sync`: Retrieve Pinecone vector DB stats and documents (read-only)
- `GET /api/files/page`: Render the file management page

## Usage

1. Start the application
2. Access the chat interface at the root URL (`/`)
3. Access the file management interface at `/api/files/page`
4. Upload files through the UI or place them directly in the knowledge-base directory
5. Ask questions in the chat interface to get answers based on the knowledge base

### Chat Interface Structure

Responses follow a streamlined format:

1. **Main Answer**: Primary response with real-time markdown rendering
2. **Next Steps**: Optional buttons suggesting follow-up prompts

## Logging

The application includes comprehensive logging for debugging and monitoring:
- Chat conversations with user queries and AI responses
- RAG retrieval with document scores and content previews
- API calls to OpenAI including token usage
- File uploads with embedding generation details
- Semantic search results with similarity percentages

Logging configuration is centralized in config.py, making it easy to adjust log levels and formats across the entire application without modifying individual files.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.