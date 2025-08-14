## RAG Agent Generalization – Implementation Plan (Migrations)

This plan migrates the current client-specific app into a neutral, user-configurable, local-first RAG chatbot. It is written to be executed incrementally, with clear success criteria, testing, and debugging guidance for each chunk of work. The end objective is a super user-friendly app that anyone can run locally, customize via a settings UI, and persist data across sessions.

Guiding principles
- No hardcoded defaults in model/agent behavior: all LLM and agent parameters must come from user-provided settings. If not configured, the app presents a blocking setup screen (no silent fallbacks).
- Local-first persistence: SQLite database file and local static assets persist across restarts. Vector data persists in Pinecone.
- Neutral branding by default; theming is configurable via settings, not code edits.
- Modular services, minimal dependencies; transparent logs for debugging.
- Tests accompany each change; lint/format enforced via a make target.

Scope highlights
- Neutral branding and theming; remove client-specific copy/assets.
- Multi-agent registry: users can add/edit agents (name, role/system prompt, model, temperature, max tokens, selection rules).
- Settings page + first-run setup wizard to configure everything (OpenAI, Pinecone, LLM params, theme, chunking sizes, DB selection, etc.).
- Remove “resources” UI from chat; responses are simplified to main answer (+ optional next steps).
- SQLite by default; Postgres optional via `DATABASE_URL`. No Postgres-only types in models.
- Add ingestion support for JSON, TXT, MD/Markdown, JSONL, CSV, DOCX, PDF, Excel (XLSX).
- Remove Replit artifacts; switch to venv + Makefile; MIT license; pytest tests.

Architecture overview updates
- Config runtime source becomes the Settings store (SQLite), not `config.py` constants.
- New `settings_service.py` responsible for reading/writing validated settings.
- New `agent_registry.py` for CRUD and runtime selection; agents stored in DB.
- Existing services (`pinecone_service`, `embeddings_service`, `file_service`) read parameters from settings.
- First-run wizard blocks app until minimal required settings are supplied and validated.

---

### Chunk 1 — Configuration & Persistence Foundation

Changes
- Add `settings` table: `key (str, PK)`, `value (JSON)`, `updated_at (datetime UTC)`. Provide typed accessors in `settings_service.py` with validation.
- Migrate runtime config to settings: app/brand name, theme colors, OpenAI model/temperature/max tokens, embedding model, Pinecone keys/index/dimension/metric/region, chunk size/overlap, allowed file types, UI copy, and feature flags.
- Default database: `sqlite:///rag_agent.db` (file in project root). Allow optional Postgres via `DATABASE_URL`.
- Replace Postgres JSON dialect usage with portable `sqlalchemy.JSON` across models.
- Add health endpoint `/health` returning app readiness and configured/required settings status.

Success criteria
- App starts against SQLite; tables auto-create; `/health` returns 200 with readiness=false until required settings exist.
- No import of `sqlalchemy.dialects.postgresql.JSON` anywhere.
- Settings can be read/written via `settings_service` and are persisted.

Testing
- Unit: `settings_service` CRUD; type validation; missing required values returns explicit errors.
- Integration: App boots, `/health` shows missing keys; after inserting settings (fixture), `/health` shows ready.

Debugging
- Add logs at settings load time with key names only (never secrets). Log validation failures with actionable messages.

Guidelines/Patterns
- Do not read model/agent parameters from `config.py`. Only use `settings_service`.
- Use `datetime.utcnow()` for timestamps.

---

### Chunk 2 — Neutral Branding & Theming

Changes
- Replace client names/assets in `templates/` and `static/` with neutral labels sourced from settings: brand name, logo URL (optional), theme colors.
- Inject UI text (welcome message, predefined prompts) from settings.
- Remove client-specific colors; define CSS variables computed from settings.

Success criteria
- UI renders with neutral name/theme set in settings; changing settings reflects immediately after refresh.

Testing
- Snapshot UI strings and CSS variables via a simple DOM test (pytest + selenium optional later) or route-rendered HTML assertions.

Debugging
- Log current theme keys on server start; validate color hex formats when saving settings.

Guidelines/Patterns
- Keep templates free of client copy; pull everything from settings injection.

---

### Chunk 3 — Multi-Agent Registry & Selection

Changes
- New tables: `agents (id, name, description, role_system_prompt, llm_model, temperature, max_tokens, response_format, selection_rules JSON, created_at, updated_at)`.
- `agent_registry.py`: CRUD APIs and runtime selection: given retrieved docs and/or user query, evaluate `selection_rules` (e.g., doc metadata `doc_type` match). Provide a default rule set users can edit.
- `agno_service` becomes a thin orchestrator: builds messages from agent config + retrieved docs; calls OpenAI using the agent’s parameters. Remove hardcoded JSON response keys; keys come from settings (but enforce schema in UI).
- `chat_routes`: replace ad-hoc event loop with synchronous call path; selection uses registry; return `{ response, next_steps? }` only.

Success criteria
- User can create at least two agents via settings page (e.g., “Documentation” and “Course”) with different prompts/models.
- Queries pick agents according to rules with no code changes.

Testing
- Unit: `agent_registry` rule evaluation (doc_type, keyword match) and CRUD.
- Integration: create agents via API, ask queries that route to different agents; assert selected agent names.

Debugging
- Log evaluated rules and final selection for each chat request (without logging user content).

Guidelines/Patterns
- No fallback agent. If no rule matches, return a 400 with a clear message or prompt the user to define a default rule in settings.

---

### Chunk 4 — Ingestion Pipeline (DOCX, PDF, XLSX)

Changes
- Extend allowed file types: `txt, md, json, jsonl, csv, docx, pdf, xlsx` (and optionally `xls`).
- Implemented parsers in `services/file_service.extract_text_and_metadata`:
  - TXT/MD: pass-through.
  - JSON/JSONL: safe load + pretty-print; infer `doc_type` from keys (`doc_type`, `type`, `Category`, `Type`).
  - CSV: parse header + rows; pretty-print; infer `doc_type` from a header column.
  - XLSX: `openpyxl` read-only; emit per-sheet headers and rows; infer `doc_type` from header/first data row.
  - DOCX: `python-docx` paragraphs concatenated.
  - PDF: `pypdf` per-page extraction; attempt empty-password decrypt; clear error for encrypted PDFs.
- Normalize metadata and upsert to Pinecone with `type` set from document metadata; chunking via `utils.embeddings.chunk_text` (sizes from settings).

Success criteria
- Uploading each supported type succeeds; chunks get created; Pinecone upserts succeed; semantic search returns content.

Testing
- To follow in Chunk 8. Interim: manual upload of each type; lints/tests green with providers unconfigured.

Debugging
- Parser-level logs with file name, pages/rows processed, and truncation notes. No content logs beyond small previews.

Guidelines/Patterns
- Fail fast with clear error messages if a library is missing; surface install guidance in the UI.

---

### Chunk 5 — Settings UI & First-Run Wizard

Changes
- Added `/settings` template with tabbed UI for General, Providers (OpenAI/Pinecone), RAG, Agents (read-only list for now), Diagnostics.
- First-run gating: `/` redirects to `/settings` until readiness passes (`services.settings_service.readiness`).
- New Settings APIs in `routes/settings_routes.py`: `/api/settings` (get all), and POST endpoints for each group; `/api/settings/test/openai`, `/api/settings/test/pinecone`, and `/api/diagnostics`.

Success criteria
- On first run, wizard appears; “Test OpenAI” and “Test Pinecone” succeed with correct keys; app transitions to ready state.
- Subsequent visits allow editing settings and agents; changes persist.

Testing
- To follow in Chunk 8. Interim: diagnostics endpoint returns readiness and provider checks; manual validation.

Debugging
- Add `/diagnostics` API that runs end-to-end checks (OpenAI, Pinecone, DB write/read) and returns a structured report.

Guidelines/Patterns
- Do not embed any vendor defaults; users must explicitly pick models and set API keys before use.

---

### Chunk 6 — Chat UI Simplification (Remove Resource Cards)

Changes
- Removed resource card rendering from `static/js/chat.js`. Answers render as markdown; optional next_steps shown as buttons.

Success criteria
- No references to resources remain in UI or API responses; no UI errors during chat.

Testing
- Manual: chat flow start-to-finish; verify no DOM errors.

Debugging
- Log response schema at server before returning; validate keys against settings-defined schema.

Guidelines/Patterns
- Keep UI minimal, accessible, and keyboard-friendly.

---

### Chunk 7 — Dev Experience: venv, Makefile, Lint/Format, MIT License

Changes
- Add `Makefile` targets:
  - `make venv` (create and upgrade venv), `make install`, `make run`, `make dev`, `make lint`, `make format`, `make test`, `make clean`.
- Add `ruff` and `black`; define `make_lint` to run formatting and lint checks. `Makefile` `test` target fails on errors (no silent `|| true`).
- Add `pytest` with a `tests/` folder structure.
- Add `LICENSE` (MIT) and update README accordingly.
- Remove `replit.nix`; rename project in `pyproject.toml`; add dependencies for new parsers.

Success criteria
- Fresh clone to run: `make venv && make install && make run` works on macOS.
- `make_lint` passes; `make test` passes; `LICENSE` present and referenced in README.

Testing
- CI-like local runs of `make_lint` and `make test`.

Debugging
- Ensure `ruff` rules are aligned with code style; fix high-signal issues only.

Guidelines/Patterns
- Keep dependency set minimal and pinned in `pyproject.toml`.

---

### Chunk 8 — Testing & Quality Gates

Changes
- Add tests:
  - Settings: CRUD, validation, first-run readiness.
  - Agents: CRUD, selection logic with document metadata fixtures.
  - Ingestion: unit tests per file type; integration across Pinecone upsert + search (mock embeddings when running offline).
  - Chat: route selection and response handling with an injected fake OpenAI client for deterministic outputs. (Deferred to v1.x; current tests avoid external calls.)
- Add fixtures for sample files (small, synthetic, non-sensitive).

Success criteria
- >90% coverage goal on services (tracked separately); deterministic tests without external network by default.

Testing
- Use dependency injection to swap `OpenAI` and `Pinecone` with fakes/mocks; add a `TEST_MODE` flag in settings.

Debugging
- Verbose logs in test mode; capture logs in pytest for failure triage.

Guidelines/Patterns
- Do not hit external APIs in unit tests; integration tests can be opt-in with env flag.

---

### Chunk 9 — Persistence & Data Management

Changes
- Confirm SQLite file path (`rag_agent.db`) is outside ephemeral dirs and checked in `.gitignore`.
- Ensure SQLAlchemy sessions commit after writes and rollback on errors universally.
- Add backup/export endpoint for settings (JSON download) and import (with validation):
  - GET `/api/settings/export` → settings JSON
  - POST `/api/settings/import` → applies known keys via validators; returns `{applied, errors}`

Success criteria
- Stopping/restarting the app retains all settings, agents, files metadata, conversations.
- Export/import round-trips settings without loss (validated by tests).

Testing
- Kill-and-restart manual test; verify persisted state.
- Export/import tests compare JSON snapshots (`tests/test_settings_export_import.py`).

Debugging
- Add DB connection and migration logs; include file path and size for visibility.

Guidelines/Patterns
- Avoid destructive migrations; use additive schema changes and data migrations.

---

### Chunk 10 — Cleanup & Documentation

Changes
- Remove Replit artifacts and client-specific assets.
- Update `README.md` for neutral app, setup steps (venv, Makefile), first-run wizard, and Settings.
- Add `index.md` documenting folder structure, classes, and functions with concise explanations.
- Update `BLUEPRINT.md` to reflect new architecture and flows.

Success criteria
- Repo is clean, brand-neutral, and self-explanatory to new users.

Testing
- Fresh machine dry run of setup and first-run wizard.

Debugging
- Keep a short “Troubleshooting” section in README.

---

Required new/updated modules (to be implemented)
- `services/settings_service.py`: typed getters/setters, validation.
- `services/agent_registry.py`: agent CRUD and selection.
- `routes/settings_routes.py`: REST/HTML for settings UI and first-run wizard.
- `templates/settings.html`: settings UI (tabbed interface), Diagnostics panel.
- `tests/` with unit/integration tests per chunks above.
- Update: `models.py` (portable JSON, settings and agent models), `services/file_service.py` (parsers), `services/agno_service.py` (sync), `services/pinecone_service.py` (stats/listing), `routes/chat_routes.py` (simplified response), `static/js/chat.js` (remove resources).

Dependency updates (pyproject)
- Add: `python-dotenv` (optional if we keep secrets only in DB), `ruff`, `black`, `pytest`, `python-docx`, `pypdf`, `openpyxl`.
- Keep: `flask`, `sqlalchemy`, `flask-sqlalchemy`, `openai`, `pinecone`.
- Make `psycopg2-binary` optional (only if using Postgres).

Security & privacy notes
- Keys stored locally in SQLite; optionally encrypted with a user-supplied master password (recommended). If unset, store as plain text with local-only warning.
- Never log secrets; validate with short-lived “Test” requests that redact values in logs.

Rollout strategy
- Execute chunks sequentially. After each chunk:
  - Run `make_lint` and `make test`.
  - Manually verify the success criteria.
  - Update `BLUEPRINT.md` and `README.md` delta.

Acceptance checklist
- App runs locally with SQLite by default; first-run wizard completes; chat works end-to-end.
- User can add/edit agents and settings from the UI; no code changes required for customization.
- Ingestion supports JSON, TXT, MD, JSONL, CSV, DOCX, PDF, XLSX.
- No hardcoded model parameters; all agent/LLM settings come from user input.
- Resources UI removed; UI is clean and neutral.
- Lint/tests pass; MIT license present; Replit artifacts removed.


