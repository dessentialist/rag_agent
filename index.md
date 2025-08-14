# RAG Agent – Index

This document lists the folder structure and provides a concise description of the main modules, classes, and functions.

## Folder Structure

```
rag_agent/
  app.py                 # Flask app creation, DB init, blueprint registration; injects settings into templates
  config.py              # Minimal legacy constants; SQLite default; theme defaults
  database.py            # SQLAlchemy initialization
  models.py              # ORM models: Document, DocumentChunk, Message, Conversation, Setting, Agent
  routes/
    chat_routes.py       # /api/chat, conversations CRUD; readiness guard; agent selection via registry
    file_routes.py       # /api/files endpoints; allowed types from settings
    settings_routes.py   # Settings CRUD APIs, agent CRUD, diagnostics (/api/settings/*, /api/diagnostics)
  services/
    settings_service.py  # Typed getters/setters with validation; readiness; default UI seeding
    agent_registry.py    # CRUD helpers, rule matching, default agent seeding
    agno_service.py      # generate_response(agent_cfg, query, docs) using agent params
    embeddings_service.py# OpenAI embeddings using model from settings
    pinecone_service.py  # Lazy Pinecone client/index; search/upsert/list; limits from settings
    file_service.py      # Save/lookup/delete documents; chunking and upsert to Pinecone
  utils/
    embeddings.py        # chunk_text and chunk_document; sizes from settings when not provided
  templates/
    index.html           # Neutral chat UI; theme & content injected from settings
    files.html           # Neutral files UI; brand name from settings
    settings.html        # Minimal first-run wizard & settings page (Tabbed UI calling /api/settings/*)
  static/
    css/styles.css       # Neutral theme variables; no client branding
    js/chat.js           # Chat UI logic; resource carousel removed (answers + optional next_steps only)
```

## Core Models

- Setting: key (str, PK), value (JSON), updated_at (UTC). Stores runtime configuration.
- Agent: id (int), name, description, role_system_prompt, llm_model, temperature, max_tokens, response_format, selection_rules (JSON), created_at/updated_at.
- Document/DocumentChunk: uploaded file content and chunk metadata; stored for provenance.
- Conversation/Message: chat history; timestamps in UTC.

## Key Services

- settings_service
  - get_/set_ functions for general, theme, ui, openai, embedding, pinecone, rag
  - readiness(): returns {ready, missing_keys}
  - ensure_default_ui_settings(): seeds neutral UI values

- agent_registry
  - list_agents(), create_agent(), update_agent(), delete_agent()
  - select_agent_for_request(retrieved_docs, user_query) → (agent, rules)
  - ensure_default_agents(): seeds two example agents (documentation, course)

- agno_service
  - generate_response(agent_cfg, user_query, relevant_docs): builds messages (RAG context), calls OpenAI using agent params; returns JSON dict with at least 'main'.

- pinecone_service
  - initialize_pinecone(), upsert_to_pinecone(), delete_from_pinecone(), list_all_vectors(), semantic_search()
  - Uses settings for api key, index, dimension, metric, region; lazy init

## Notable Functions

- utils.embeddings.chunk_text(text, chunk_size, chunk_overlap): chunks text; falls back to settings when None
- routes.chat_routes.chat(): validates readiness, retrieves docs, selects agent via registry, returns {response, next_steps}

## Notes

- All runtime parameters must come from settings; code avoids hardcoded model/agent defaults.
- Logs never include secrets; readiness and errors are explicit and actionable.


