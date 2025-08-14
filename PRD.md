## Product Requirements Document (PRD)

### Product: Local, User‑Configurable RAG Chatbot
### Owner: Darpan (CTO)
### Status: Draft v1.0
### Last Updated: 2025‑08‑14

---

### 1) Summary
Build a neutral, local‑first Retrieval‑Augmented Generation (RAG) chatbot that anyone can download and run on macOS using a simple Python virtual environment and Makefile. The app must be fully customizable via a settings UI (no code edits required) and persist data locally (SQLite and Pinecone). Users can define multiple agents with custom roles/parameters and selection rules. No silent fallbacks or hardcoded defaults in the model layer; all parameters must originate from user input via the settings UI or imported configurations.

---

### 2) Goals and Non‑Goals

- Goals
  - Provide an immediately usable local RAG chatbot with a simple first‑run setup wizard.
  - Enable non‑developers to configure brand/theme, providers, models, chunking, ingestion, and multi‑agent behavior from a settings page.
  - Support ingestion of TXT, MD, JSON, JSONL, CSV, DOCX, PDF, and XLSX and index chunks in Pinecone for retrieval.
  - Persist conversations, files, agents, and settings in SQLite so sessions survive restarts.
  - Lock in to OpenAI and Pinecone for now, exposed via UI (no hardcoded defaults).
  - Ship with linting, tests (pytest), and a Makefile workflow.

- Non‑Goals
  - Enterprise auth (SSO), multi‑tenant SaaS hosting.
  - Advanced analytics/telemetry beyond local diagnostics.
  - Model‑agnostic vector DB and LLM abstraction across many vendors (future work).
  - Real‑time streaming token‑by‑token UI (optional future enhancement).

---

### 3) Personas

- Local Admin (Primary)
  - Installs and runs the app locally on macOS, manages settings, adds documents, configures agents, validates providers.
  - Needs clear guidance, validation, and tests in the UI.

- Knowledge Worker (Secondary)
  - Uses the chat interface to ask questions. Expects concise, accurate answers grounded in uploaded content.

---

### 4) Key Use Cases

1. First‑run setup
   - On first launch, user sees a wizard to set OpenAI and Pinecone keys, choose models, define a default agent, set chunking, brand/theme, and test connections.

2. Multi‑agent configuration
   - User adds multiple agents, each with name, description, role/system prompt, LLM model, temperature, max tokens, response schema, and selection rules (e.g., select when `doc_type == "documentation"`).

3. Document ingestion
   - User uploads supported files; system extracts text, chunks per settings, and upserts to Pinecone with normalized metadata.

4. Ask questions
   - User asks a question; app retrieves relevant chunks, selects an agent via rules, invokes the LLM, and returns a structured answer.

5. Review and manage
   - User lists files, views metadata, deletes files (and associated vectors), reviews conversations, exports/imports settings.

---

### 5) Scope and Features

- Settings & Wizard
  - Sections: General (brand, theme), Providers (OpenAI, Pinecone), LLM defaults, Agents (CRUD), RAG (chunk size/overlap, limits), Database (SQLite/Postgres), Advanced (feature flags), Diagnostics (test connections).
  - First‑run wizard blocks usage until required fields are provided and validated.
  - No default vendor/model values are baked into agent/model execution; the wizard or settings must explicitly capture choices.

- Multi‑Agent Registry
  - CRUD UI and APIs for agents with fields: name, description, role/system prompt, llm_model, temperature, max_tokens, response_format, selection_rules (JSON), timestamps.
  - Selection rules evaluate retrieved document metadata and/or query attributes to choose the agent; no implicit fallback. If nothing matches, return an actionable error prompting configuration.

- Chat
  - Clean interface with welcome message and optional next‑steps buttons.
  - No resource carousel/cards. Answers are markdown; next steps are optional.

- Ingestion
  - Supported: TXT, MD, JSON, JSONL, CSV, DOCX, PDF, XLSX. Robust parsing with friendly errors.
  - Normalized chunk metadata: `doc_type`, `source_filename`, `title`, `url` (local file route), `chunk_index`, `total_chunks`.
  - Configurable chunk size and overlap.

- Storage & Persistence
  - SQLite (`rag_agent.db`) by default with SQLAlchemy; optional Postgres via `DATABASE_URL`.
  - Pinecone stores embeddings; index creation/validation via settings.
  - Conversations, files, chunks, agents, settings persist across restarts.

- Diagnostics
  - `/health` and diagnostics panel validate keys, index connectivity, DB read/write, and embedding/LLM readiness without leaking secrets.

- Dev Experience
  - Makefile targets for venv, install, run, lint, format, test.
  - MIT license. Pytest test suite.

---

### 6) Requirements

- Functional Requirements
  - First‑run wizard must prevent chat access until required settings pass diagnostics.
  - Settings page must allow full CRUD for agents and update of all parameters described above.
  - Upload endpoint must accept and process all supported file types; failures are precise and actionable.
  - Chat endpoint must select an agent solely via selection rules; no implicit defaults in execution.
  - Delete file must remove related vectors in Pinecone and chunks in DB.
  - Export/import settings to JSON with validation.

- Non‑Functional Requirements
  - Local deployment on macOS (Apple Silicon) with Python 3.11+.
  - Performance: answers typically < 5s on broadband (LLM‑bound). Ingestion < 30s for typical files (<10MB) on a warmed index.
  - Reliability: clear error handling, no server crashes on bad inputs; always rollback DB transactions on failure.
  - Security & Privacy: secrets stored locally; never logged; local‑only diagnostics; optional master password for secret encryption (future enhancement).
  - Accessibility: keyboard navigation, proper semantics, color contrast aligned with WCAG AA where feasible.
  - Internationalization: copy is minimal and can be altered via settings; UI labels are not hard‑coded in business logic.

---

### 7) UX & Interaction Requirements

- First‑Run Wizard Flow
  1. Welcome → explain requirements and local‑first model.
  2. Providers → OpenAI key, Pinecone key, environment/region, index name; buttons: Test OpenAI, Test Pinecone.
  3. LLM Defaults → embedding model, chat model, temperature, max tokens.
  4. Agent Setup → create at least one agent (fields above) and define a default selection rule.
  5. RAG → chunk size/overlap, allowed types.
  6. Brand/Theme → app name, optional logo, primary/secondary colors.
  7. Finish → run diagnostics; only then enable chat and files sections.

- Settings Page
  - Tabbed interface mirroring the wizard sections; includes Diagnostics panel with real‑time checks.
  - Edits require explicit Save; validation prevents inconsistent states.

- Chat Page
  - Minimal UI: messages list, input, send; agent indicator; optional next‑steps.
  - No resource carousel.

- Files Page
  - Drag‑and‑drop uploads; show progress; list Pinecone document stats; search/filter; view preview; delete.

---

### 8) Data Model (High‑Level)

- settings: key (str, PK), value (JSON), updated_at (datetime)
- agents: id (int), name, description, role_system_prompt, llm_model, temperature, max_tokens, response_format (string), selection_rules (JSON), created_at, updated_at
- documents: id (str), filename, file_type, content (text), metadata (JSON), created_at
- document_chunks: id (str), document_id (fk), chunk_index (int), content (text), vector_id (str), created_at
- conversations: id (str), created_at, updated_at
- messages: id (int), conversation_id (fk), role (str), content (text), timestamp

Note: Use portable `sqlalchemy.JSON` (not Postgres‑specific types). Timestamps use UTC.

---

### 9) Dependencies & Constraints

- External
  - OpenAI (chat + embeddings) – user provides keys/models.
  - Pinecone – user provides keys/env/index; index created/validated from settings.

- Python Libraries (initial)
  - Flask, SQLAlchemy, Flask‑SQLAlchemy, OpenAI SDK, Pinecone SDK, python‑docx, pypdf, openpyxl, requests, ruff, black, pytest.

- Constraints
  - No Docker in default path; use venv + Makefile.
  - No hidden defaults for models; wizard/settings must define them.

---

### 10) Acceptance Criteria & Success Metrics

- Acceptance Criteria
  - AC1: Fresh clone → `make venv && make install && make run` → wizard blocks until keys/models entered and diagnostics pass.
  - AC2: User creates two agents with different prompts/models and rules; queries route to the correct agent without code edits.
  - AC3: User uploads a PDF, DOCX, and XLSX; chunks are created; Pinecone stats update; search retrieves relevant text.
  - AC4: Restarting the app preserves settings, agents, conversations, and files; Pinecone data persists.
  - AC5: No resource UI appears; chat answers and next‑steps render correctly.
  - AC6: `make_lint` and `make test` pass locally.

- Success Metrics (initial)
  - Time to first successful chat from fresh install < 10 minutes.
  - Ingestion success rate > 99% for supported types under 10MB.
  - > 90% unit/integration coverage on services.
  - < 1% unhandled exceptions during typical usage flows.

---

### 11) Release Plan & Milestones

- M1: Configuration & Persistence Foundation (settings store, SQLite default, health/diagnostics)
- M2: Neutral Branding & Theming
- M3: Multi‑Agent Registry & Selection
- M4: Ingestion for DOCX/PDF/XLSX (plus existing types)
- M5: Settings UI & First‑Run Wizard
- M6: Chat UI Simplification (remove resources)
- M7: Dev Experience (Makefile, lint/format, pytest, MIT)
- M8: Testing & Quality Gates
- M9: Documentation & Cleanup

Each milestone must meet its success criteria and ship with tests and documentation updates.

---

### 12) Risks & Mitigations

- Risk: Users omit required settings and expect app to “just work”.
  - Mitigation: Hard block via wizard; prominent diagnostics with guidance.

- Risk: PDF/DOCX/XLSX parsing edge cases causing poor text extraction.
  - Mitigation: Use proven libraries; surface clear errors; document limitations; allow re‑ingestion.

- Risk: Pinecone listing at scale.
  - Mitigation: Show stats and sampled listings; pagination; avoid querying entire index.

- Risk: Users paste secrets into logs by accident.
  - Mitigation: Never log secrets; redact inputs; add copy hints in UI.

---

### 13) Out of Scope (for v1)

- User authentication/multi‑user roles.
- Cloud deployment templates.
- Streaming UI and advanced conversation tools (citations in‑line, code‑exec, etc.).

---

### 14) Open Questions

- Should we support an optional master password to encrypt stored secrets in SQLite in v1 or v1.x?
- Do we need export/import for agents alongside settings in a single bundle file?
- Any minimum viable accessibility expectations beyond keyboard and color contrast?

---

### 15) Appendix

- Glossary
  - RAG: Retrieval‑Augmented Generation – LLM responses grounded in retrieved documents.
  - Agent: A configured set of LLM parameters and a role/system prompt plus selection rules to determine when to use it.
  - First‑run Wizard: Guided flow that ensures configuration before use.

- Compliance
  - License: MIT (project ships with `LICENSE`).
  - Data: Remains local (SQLite, Pinecone). No external telemetry.


