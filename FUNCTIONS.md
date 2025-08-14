# BigID University - AI Tutor Function Documentation

This document provides detailed information about the functions and components of the BigID University AI Tutor application. It serves as a technical reference for developers working with the codebase.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Main Application](#main-application)
3. [Database Models](#database-models)
4. [Services](#services)
   - [Agno Service](#agno-service)
   - [Embeddings Service](#embeddings-service)
   - [File Service](#file-service)
   - [Pinecone Service](#pinecone-service)
5. [Routes](#routes)
   - [Chat Routes](#chat-routes)
   - [File Routes](#file-routes)
6. [Utilities](#utilities)
   - [Embeddings Utilities](#embeddings-utilities)

## Project Structure

The application follows a modular architecture with the following components:

- **Main Application**: Entry point and configuration
- **Database Models**: Data structures
- **Services**: Business logic implementation
- **Routes**: API endpoints
- **Utilities**: Helper functions

## Main Application

### `main.py`

- **Purpose**: Application entry point
- **Functions**: 
  - Imports the Flask app from app.py

### `app.py`

- **Purpose**: Flask application configuration
- **Functions**:
  - Creates and configures the Flask application
  - Sets up SQLAlchemy and database connection
  - Initializes the database tables

### `config.py`

- **Purpose**: Centralized configuration settings
- **Sections**:
  - **Logging Configuration**:
    - `LOG_LEVEL`: Sets logging level for the application
    - `LOG_FORMAT`: Defines format string for log messages
  
  - **Flask and Database Configuration**:
    - `SESSION_SECRET`: Secret key for Flask sessions
    - `SERVER_HOST`: Host address for the server
    - `SERVER_PORT`: Port number for the server
    - `DEBUG_MODE`: Flag for Flask debug mode
    - `DATABASE_URI`: PostgreSQL connection string
    - `DATABASE_POOL_RECYCLE`: Connection pool recycling time
    - `DATABASE_POOL_PRE_PING`: Flag for connection health checks
    - `DATABASE_TRACK_MODIFICATIONS`: Flag for SQLAlchemy event tracking
  
  - **API Keys and External Service Configurations**:
    - `OPENAI_API_KEY`: API key for OpenAI
    - `EMBEDDING_MODEL`: Model for generating embeddings
    - `LLM_MODEL`: OpenAI model for chat completions
    - `LLM_TEMPERATURE`: Temperature parameter for response generation
    - `LLM_MAX_TOKENS`: Maximum tokens for AI responses
    - `LLM_RESPONSE_FORMAT`: Format specification for API responses
    - `PINECONE_API_KEY`: API key for Pinecone
    - `PINECONE_ENVIRONMENT`: Pinecone environment
    - `PINECONE_INDEX_NAME`: Name of the Pinecone index
    - `PINECONE_DIMENSION`: Dimension for vector embeddings
    - `PINECONE_METRIC`: Similarity metric for vector search
    - `PINECONE_CLOUD`: Cloud provider for Pinecone
    - `PINECONE_REGION`: Region for Pinecone hosting
    - `PINECONE_SEARCH_LIMIT`: Default limit for search results
  
  - **File Upload and Processing Configurations**:
    - `ALLOWED_EXTENSIONS`: Set of allowed file extensions
    - `MAX_CONTENT_LENGTH`: Maximum file size for uploads
    - `KNOWLEDGE_BASE_DIR`: Directory path for knowledge base files
    - `CHUNK_SIZE`: Size of document chunks in characters
    - `CHUNK_OVERLAP`: Overlap between chunks in characters
  
  - **AI Agent Configurations**:
    - `AGENT_NAME`: Name of the AI agent
    - `AGENT_DESCRIPTION`: Description of the agent's purpose
    - `AGENT_INSTRUCTIONS`: Detailed instructions for response format and behavior
    - `AGENT_PERSONA`: How the agent views itself and its capabilities
    - `AGENT_GOAL`: Primary objective of the agent
    - `RAG_SYSTEM_MESSAGE_TEMPLATE`: Template for system messages
    - `NO_DOCUMENTS_MESSAGE`: Message when no documents are found
    - `CRITICAL_REMINDER_MESSAGE`: Reminder about using only retrieved documents
    - `AGENT_TOOLS`: Configuration for agent tools
  
  - **UI Configurations**:
    - `BOT_WELCOME_MESSAGE`: Initial message shown to users
    - `PREDEFINED_PROMPTS`: Set of predefined queries for users
    - `THEME_COLORS`: Color scheme for the UI

### `database.py`

- **Purpose**: Database initialization
- **Classes**:
  - `Base`: SQLAlchemy declarative base class

## Database Models

### `models.py`

- **Purpose**: Defines database models for SQLAlchemy
- **Classes**:
  - `Document`: Represents a file in the system
    - Attributes: id, filename, file_type, content, file_metadata, created_at
    - Relationships: chunks (Document → DocumentChunk)
    - Methods: 
      - `size()`: Returns the size of the document content
      - `to_dict()`: Converts the document to a dictionary
  
  - `DocumentChunk`: Represents a chunk of a document used for RAG
    - Attributes: id, document_id, chunk_index, content, vector_id, created_at
    - Relationships: document (DocumentChunk → Document)
    - Methods:
      - `to_dict()`: Converts the document chunk to a dictionary
  
  - `Message`: Represents a chat message
    - Attributes: id, conversation_id, role, content, timestamp
    - Relationships: conversation (Message → Conversation)
    - Methods:
      - `to_dict()`: Converts the message to a dictionary
  
  - `Conversation`: Represents a chat conversation
    - Attributes: id, created_at, updated_at
    - Relationships: messages (Conversation → Message)
    - Methods:
      - `add_message(role, content)`: Adds a message to the conversation
      - `to_dict()`: Converts the conversation to a dictionary

## Services

### Agno Service

#### `services/agno_service.py`

- **Purpose**: Implements the AI agent using OpenAI
- **Classes**:
  - `AgnoAgent`: Implementation of the AI agent
    - Methods:
      - `__init__(name, description, instructions, persona, goal)`: Initializes the agent
      - `add_tool(tool)`: Adds a tool to the agent
      - `run(query, context=None)`: Runs the agent with a query
- **Functions**:
  - `create_bigchat_agent()`: Creates a BigChat agent with provided parameters
- **Agent Instances**:
  - `course_agent`: Original agent instance for course-related documents
  - `doc_agent`: Modified agent instance that responds with brief explanations in JSON format
- **Selection Logic**:
  - `select_agent_by_doc_type(relevant_docs)`: Selects appropriate agent based on document types in retrieved documents

### Embeddings Service

#### `services/embeddings_service.py`

- **Purpose**: Handles vector embeddings generation
- **Functions**:
  - `generate_embeddings(text)`: Generates embeddings for a text using OpenAI

### File Service

#### `services/file_service.py`

- **Purpose**: Handles file operations and storage
- **Configuration Used**:
  - `KNOWLEDGE_BASE_DIR`: Path to the knowledge base directory from config.py
  - `ALLOWED_EXTENSIONS`: Set of allowed file extensions from config.py
  - `CHUNK_SIZE` and `CHUNK_OVERLAP`: Chunk parameters from config.py
- **Functions**:
  - `save_file(file_id, filename, file_type, content)`: Saves a file to the database
  - `get_all_files()`: Gets all files metadata (without content)
  - `get_file_by_id(file_id)`: Gets a file by ID
  - `delete_file_by_id(file_id)`: Deletes a file by ID
  - `scan_knowledge_base()`: Stub function that previously scanned knowledge-base directory (now disabled)
  - `process_file_for_rag(file_id, filename, content, file_type)`: Processes a file for RAG

### Pinecone Service

#### `services/pinecone_service.py`

- **Purpose**: Manages vector database operations
- **Configuration Used**:
  - `PINECONE_API_KEY`: API key from config.py
  - `PINECONE_ENVIRONMENT`: Environment from config.py
  - `PINECONE_INDEX_NAME`: Index name from config.py
  - `PINECONE_DIMENSION`: Vector dimension from config.py
  - `PINECONE_METRIC`: Similarity metric from config.py
  - `PINECONE_CLOUD`: Cloud provider from config.py
  - `PINECONE_REGION`: Region from config.py
  - `PINECONE_SEARCH_LIMIT`: Default search limit from config.py
- **Functions**:
  - `initialize_pinecone()`: Initializes Pinecone and creates the index if it doesn't exist
  - `upsert_to_pinecone(id, content, metadata=None)`: Generates embeddings and upserts to Pinecone
  - `delete_from_pinecone(id)`: Deletes a vector from Pinecone by ID
  - `semantic_search(query, limit)`: Performs semantic search using Pinecone with configurable limit

## Routes

### Chat Routes

#### `routes/chat_routes.py`

- **Purpose**: Implements chat-related API endpoints
- **Blueprint**: `chat_bp`
- **Endpoints**:
  - `POST /api/chat`: Handles chat messages from the user
    - Function: `chat()`
    - Gets or creates a conversation
    - Adds the user message to the conversation
    - Generates a response using the Agno agent
    - Formats and returns the response
  
  - `GET /api/conversations`: Gets a list of all conversations
    - Function: `get_conversations()`
  
  - `GET /api/conversations/<conversation_id>`: Gets a specific conversation by ID
    - Function: `get_conversation(conversation_id)`
  
  - `DELETE /api/conversations/<conversation_id>`: Deletes a specific conversation
    - Function: `delete_conversation(conversation_id)`

### File Routes

#### `routes/file_routes.py`

- **Purpose**: Implements file-related API endpoints
- **Blueprint**: `files_bp`
- **Helper Functions**:
  - `allowed_file(filename)`: Checks if a file extension is allowed
- **Endpoints**:
  - `POST /api/files/upload`: Uploads a new file
    - Function: `upload_file()`
    - Validates and processes uploaded files
    - Saves files to the database and knowledge base directory
    - Processes files for RAG
  
  - `GET /api/files`: Gets a list of all files
    - Function: `get_files()`
  
  - `GET /api/files/<file_id>`: Gets a specific file
    - Function: `get_file(file_id)`
  
  - `DELETE /api/files/<file_id>`: Deletes a specific file
    - Function: `delete_file(file_id)`
  
  - `DELETE /api/files`: Deletes all files
    - Function: `delete_all_files()`
  
  - `POST /api/files/sync`: Syncs with the knowledge-base directory
    - Function: `sync_knowledge_base()`
    - Scans the knowledge-base directory
    - Imports new files into the database
  
  - `GET /api/files/page`: Renders the file management page
    - Function: `files_page()`

## Utilities

### Embeddings Utilities

#### `utils/embeddings.py`

- **Purpose**: Provides utilities for text chunking
- **Constants**:
  - `CHUNK_SIZE`: Maximum chunk size in characters (default: 1000)
  - `CHUNK_OVERLAP`: Overlap between chunks in characters (default: 200)
- **Functions**:
  - `chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)`: Splits text into chunks
  - `chunk_document(doc_id, content, metadata=None)`: Chunks a document for vector storage

## Frontend Components

### Chat Interface

#### `static/js/chat.js`

- **Purpose**: Implements the client-side chat functionality
- **Functions**:
  - `handleChatSubmit(event)`: Handles chat form submission
  - `addUserMessage(message)`: Adds a user message to the chat
  - `addBotMessage(message, withTypingEffect)`: Adds a bot message to the chat
  - `addTypingIndicator()`: Adds a typing indicator
  - `typeMessage(element, message, speed)`: Types out a message with real-time markdown rendering
  - `addResourceCarousel(resources)`: Adds a carousel of resources to the last message
  - `scrollToBottom()`: Scrolls the chat to the bottom
  - `addSuggestedTopics()`: Adds suggested topics with clickable buttons
  - `addNextSteps(steps, targetElement)`: Adds interactive next step buttons
    - When called with targetElement, adds next steps to an existing message element
    - When called without targetElement, creates a standalone container for next steps

### File Manager

#### `static/js/fileManager.js`

- **Purpose**: Implements the client-side file management functionality
- **Core Variables**:
  - `fileList`: Reference to the document list container (aliased from pineconeFileList)
  - `searchButton`: Reference to the search button in the file management interface
- **Functions**:
  - `handleFileUpload(event)`: Handles file upload form submission
  - `uploadMultipleFiles(files)`: Uploads multiple files sequentially
  - `uploadSingleFile(file)`: Uploads a single file with progress tracking
  - `handleDragOver(event)`: Handles drag over events for drag-and-drop functionality
  - `handleDrop(event)`: Handles drop events for drag-and-drop file uploads
  - `showUploadStatus(type, message)`: Shows upload status with color-coded feedback
  - `loadFiles()`: Loads the list of files from the server
  - `loadPineconeDocuments()`: Loads document information from Pinecone vector database
  - `formatFileSize(bytes)`: Formats file size in human-readable format
  - `viewFile(fileId)`: Views a file's content
  - `deleteFile(fileId, filename)`: Deletes a file with confirmation
  - `deleteAllFiles()`: Deletes all files with confirmation
  - `syncKnowledgeBase()`: Refreshes Pinecone vector database information
  - `filterPineconeDocuments(query)`: Filters documents by search query

## Enhanced Logging System

The application includes comprehensive logging for debugging and monitoring:

### Chat Logging
- User queries with conversation ID
- AI responses (truncated for readability)
- Number of resources returned
- Conversation ID for tracking

### RAG Logging
- Documents retrieved from vector database
- Document scores and similarity percentages
- Content previews of retrieved documents
- Source files and chunk information

### API Call Logging
- OpenAI API calls with model information
- Token usage statistics
- Message structure information

### File Operation Logging
- File uploads and processing steps
- File renames and path changes
- Number of chunks created per file

### Embedding Logging
- Content information for embedding generation
- Vector dimensions
- Upsert confirmations
- Source file and chunk metadata

This enhanced logging system provides detailed visibility into the operation of all components, making it easier to debug issues and understand the application's behavior.

## UI Response Structure

The chat interface organizes bot responses in a structured format with multiple sections:

### 1. Main Message Content
- Primary text response to the user's query
- Displayed with a typing animation featuring real-time markdown rendering
- Formatted text (bold, italic, etc.) appears immediately as each character is typed
- Supports code blocks with syntax highlighting during typing

### 2. Next Steps Section
- Interactive blue buttons with arrow icons
- Clicking buttons submits the text as a new query
- Integrated directly within the bot message container
- No header text displayed for a cleaner interface

### 3. Resources Section
- "Resources" header
- Resource cards with title, description, and preview button
- Links to external resources
- Displayed at the end of the message

The rendering order ensures a natural reading flow and encourages deeper exploration of topics through the suggested next steps and resources.