# RAG Agent – Blueprint

This document serves as a working record of changes, decisions, and development progress for the BigID University AI Tutor application. It will be updated as the project evolves to maintain a comprehensive record of the system architecture and implementation decisions.

**Last Updated:** August 14, 2025

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Component Descriptions](#component-descriptions)
5. [API Endpoints](#api-endpoints)
6. [Integration Points](#integration-points)
7. [Development Roadmap](#development-roadmap)
8. [Change Log](#change-log)
9. [Configuration Management](#configuration-management)
10. [Testing Strategy](#testing-strategy)

## Project Overview

This project is a neutral, local‑first, configurable RAG chatbot. It leverages Retrieval‑Augmented Generation (RAG) for intelligent interaction with a local knowledge base. The system allows users to:

- Upload and manage documents related to BigID University
- Chat with an AI assistant that provides answers based on the knowledge base
- Automatically sync files between the database and the file system
- Perform semantic searches across document content

### Key Features

- **Intelligent Chatbot Interface**: Ask questions about BigID and receive accurate answers based on the knowledge base (resource cards removed; optional next-steps retained)
- **Document Management**: Upload, view, and delete files (supports TXT, MD, JSON, JSONL, CSV, DOCX, PDF, XLSX)
- **Database Storage**: Files uploaded through the UI are saved directly to the database
- **Vector Database Storage**: Document chunks are stored in Pinecone vector database for semantic retrieval
- **Semantic Search**: Uses vector embeddings to find the most relevant information for user queries
- **Comprehensive Logging**: Detailed logs for chat conversations, RAG retrieval, API calls, file operations, and vector operations
- **Centralized Configuration**: Runtime settings are stored in SQLite and accessed via `services/settings_service.py` (no hardcoded defaults in execution paths)

## System Architecture

The application follows a modular architecture with clean separation between components:

- **Frontend**: HTML/CSS/JavaScript interface with separate pages for chat and file management
- **Backend**: Flask-based Python server with RESTful API endpoints
- **Database**: SQLite by default via SQLAlchemy (Postgres optional via `DATABASE_URL`)
- **Vector Storage**: Pinecone vector database for semantic search capabilities
- **Document Storage**: Stored in the same RDBMS (SQLite by default) via SQLAlchemy models
- **AI Services**: OpenAI API integration for embeddings and LLM capabilities

### Architecture Diagram

```
+-------------------+     +-------------------+
|                   |     |                   |
|  Web Interface    |<--->|  Flask Server     |
|  (HTML/JS/CSS)    |     |  (Python)         |
|                   |     |                   |
+-------------------+     +--------+----------+
                                  |
                                  v
                          +-------------------+     +-------------------+
                          |                   |     |                   |
                           |  SQLite/Postgres  |<--->|  Pinecone         |
                          |  Database         |     |  Vector Database  |
                          |                   |     |                   |
                          +-------------------+     +-------------------+
                                  ^
                                  |
                          +-------+----------+
                          |                  |
                          |  OpenAI API      |
                          |  (Embeddings/LLM)|
                          |                  |
                          +------------------+
```

## Database Schema

The application uses SQLite by default with the following tables (portable JSON types via SQLAlchemy):

### Documents Table
Stores information about uploaded files in the knowledge base.

| Column        | Type      | Description                         |
|---------------|-----------|-------------------------------------|
| id            | String    | Primary key, unique identifier      |
| filename      | String    | Name of the uploaded file           |
| file_type     | String    | Type/extension of the file          |
| content       | Text      | Content of the file                 |
| file_metadata | JSON      | Additional metadata about the file  |
| created_at    | DateTime  | Timestamp of file creation          |

### Document_Chunks Table
Stores individual chunks of documents for RAG processing.

| Column       | Type      | Description                                     |
|--------------|-----------|-------------------------------------------------|
| id           | String    | Primary key, unique identifier                  |
| document_id  | String    | Foreign key reference to documents.id           |
| chunk_index  | Integer   | Index of the chunk within the document          |
| content      | Text      | Content of the chunk                            |
| vector_id    | String    | ID of the vector in Pinecone                    |
| created_at   | DateTime  | Timestamp of chunk creation                     |

### Conversations Table
Stores chat conversations between users and the AI.

| Column      | Type      | Description                         |
|-------------|-----------|-------------------------------------|
| id          | String    | Primary key, unique identifier      |
| created_at  | DateTime  | Timestamp of conversation creation  |
| updated_at  | DateTime  | Timestamp of last update            |

### Messages Table
Stores individual messages within conversations.

| Column          | Type      | Description                                  |
|-----------------|-----------|----------------------------------------------|
| id              | Integer   | Primary key, auto-incrementing ID            |
| conversation_id | String    | Foreign key reference to conversations.id    |
| role            | String    | Role of the message sender (user/assistant)  |
| content         | Text      | Content of the message                       |
| timestamp       | DateTime  | Timestamp of message creation                |

## Component Descriptions

### Main Application Components

1. **app.py**: Flask application setup and database configuration
2. **config.py**: Centralized configuration for the entire application
3. **database.py**: Database initialization and base model definitions
4. **main.py**: Application entry point
5. **models.py**: Database model definitions (Documents, DocumentChunks, Messages, Conversations)

### Services

1. **agno_service.py**: Implementation of AI agent for chat interactions
   - `AgnoAgent` class with methods for processing user queries
   - Multiple agent instances for different document types:
     - `course_agent`: Standard agent for course-related content
     - `doc_agent`: Modified agent providing brief explanations in JSON format
   - Dynamic agent selection based on document content
   - Structured JSON response formatting
   
2. **embeddings_service.py**: Vector embedding generation for semantic search
   - Uses OpenAI API for creating embeddings
   - Processes text into vector representations
   
3. **file_service.py**: File operations and management
   - File saving/retrieval from both database and filesystem
   - Two-way synchronization between database and knowledge-base directory
   - File processing for RAG integration
   
4. **pinecone_service.py**: Vector database operations
   - Index initialization and management
   - Vector storage and retrieval
   - Semantic search functionality

### Routes

1. **chat_routes.py**: Chat-related API endpoints
   - Chat message processing
   - Conversation management (create/get/delete)
   
2. **file_routes.py**: File management API endpoints
   - File uploading
   - File listing/retrieval
   - File deletion
   - Knowledge base synchronization

### Utilities

1. **embeddings.py**: Utilities for text processing
   - Text chunking for RAG
   - Document chunking with metadata

## API Endpoints

### Chat API

- `POST /api/chat`: Send a message to the AI and receive a response
- `GET /api/conversations`: Get a list of all conversations
- `GET /api/conversations/<conversation_id>`: Get a specific conversation by ID
- `DELETE /api/conversations/<conversation_id>`: Delete a specific conversation

### File API

- `POST /api/files`: Upload a new file
- `GET /api/files`: Get a list of all files
- `GET /api/files/<file_id>`: Get a specific file by ID
- `DELETE /api/files/<file_id>`: Delete a specific file
- `DELETE /api/files`: Delete all files
- `POST /api/files/sync`: Sync knowledge base with database

## Integration Points

### External Services

1. **OpenAI API**
   - Used for: Generating text embeddings and LLM responses
   - Configuration: API key in environment variables, model selection in config.py
   - Error handling: Comprehensive logging of API errors

2. **Pinecone Vector Database**
   - Used for: Storing and retrieving vector embeddings for semantic search
   - Configuration: API key, environment, index name in environment variables
   - Index setup: Automatic creation/validation on application startup

### Storage Systems

1. **SQLite (default) or PostgreSQL Database**
   - Purpose: Primary storage for settings, agents, conversations, files, and chunks
   - Tables: Settings, Agents, Documents, DocumentChunks, Conversations, Messages
   
2. **Pinecone Vector Database**
   - Purpose: Stores vector embeddings for semantic search
   - Content: Document chunks with metadata for retrieval

## Development Roadmap

### Current Sprint (April 2025)
- [ ] Improve RAG retrieval accuracy with advanced chunking strategies

### Backlog
- [ ] Add CSV/XLS import for batch document processing
- [ ] Add support for multimedia content in knowledge base
- [ ] Implement advanced analytics on user interactions

## Change Log

### Version 1.5 (Aug 14, 2025)
- ✅ Added ingestion for DOCX, PDF, and XLSX with robust parsers and metadata normalization
- ✅ Introduced Settings UI (`/settings`) with diagnostics and first-run gating via `/api/health`
- ✅ Simplified Chat UI by removing resource cards; retained answers + optional next steps
- ✅ Extended API: `/api/settings/*`, `/api/settings/test/*`, `/api/diagnostics`

### Version 1.4 (May 12, 2025)
- ✅ Modified doc_agent to respond with brief explanations in JSON format
- ✅ Fixed file upload process by addressing JavaScript reference errors
- ✅ Improved frontend file handling by unifying search functionality
- ✅ Enhanced agent selection logic to provide different response formats based on document types

### Version 1.3 (May 12, 2025)
- ✅ Removed two-way file synchronization between database and knowledge-base directory
- ✅ Simplified file storage to use only the database
- ✅ Updated architecture to remove filesystem dependencies
- ✅ Improved system reliability by eliminating potential file system conflicts

### Version 1.2 (April 29, 2025)
- ✅ Removed "Related Concepts" section from chat interface to streamline responses
- ✅ Modified predefined prompts to display only titles without descriptions
- ✅ Increased predefined prompt font size (1.25rem) and improved padding
- ✅ Enhanced markdown rendering for real-time formatting as text is typed
- ✅ Improved UI component flow:
  - Main message (with real-time markdown rendering)
  - Next steps (interactive suggestion buttons)
  - Resources section (with resource cards)

### Version 1.1 (April 29, 2025)
- ✅ Enhanced chat interface with structured response sections
- ✅ Improved UI component rendering order
- ✅ Optimized animations and transitions between UI components

### Version 1.0 (Initial Development)
- ✅ Basic Flask application setup
- ✅ Database models implementation
- ✅ Chat interface with AI integration
- ✅ File management system
- ✅ Knowledge base synchronization
- ✅ RAG implementation with Pinecone
- ✅ Comprehensive configuration system

## Configuration Management

The application uses a centralized configuration approach with all settings defined in `config.py`. This includes:

1. **Logging Configuration**
   - Log levels and formats

2. **Flask and Database Configuration**
   - Server settings
   - Database connection parameters

3. **API Keys and External Services**
   - OpenAI API configuration
   - Pinecone configuration

4. **File Upload and Processing**
   - Allowed file types
   - Maximum content lengths
   - Knowledge base directory location
   - Chunking parameters for RAG

5. **AI Agent Configuration**
   - Agent identity and behavior
   - Instructions and system prompts
   - Response templates

6. **UI Configuration**
   - Welcome messages
   - Predefined prompts
   - Theme colors

## Testing Strategy

The application should follow a comprehensive testing strategy including:

1. **Unit Testing**
   - Service-level function testing
   - Model validation
   - Utility function verification

2. **Integration Testing**
   - API endpoint testing
   - Database interaction testing
   - External service integration testing

3. **End-to-End Testing**
   - Complete user flow scenarios
   - UI interaction testing

4. **Performance Testing**
   - Response time measurements
   - Database query optimization
   - File processing efficiency

---

This blueprint will be updated regularly as the application evolves to ensure it remains an accurate and valuable reference for the development team.