PYTHON=python3
VENV=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

# Network defaults (override with: make run PORT=5001 HOST=127.0.0.1)
PORT?=5000
HOST?=0.0.0.0

.PHONY: venv install run dev lint format test clean make_lint

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e .

run: install
	@FREE_PORT=$$( \
		for p in `seq $(PORT) $$(( $(PORT) + 50 ))`; do \
			if ! lsof -iTCP:$$p -sTCP:LISTEN >/dev/null 2>&1; then echo $$p; break; fi; \
		done \
	); \
	echo "Using port $$FREE_PORT"; \
	FLASK_APP=app.py FLASK_RUN_HOST=$(HOST) FLASK_RUN_PORT=$$FREE_PORT $(PY) -m flask run --debug

dev:
	FLASK_APP=app.py $(PY) -m flask run --debug

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/black .

test:
	$(PY) -m pytest -q

clean:
	rm -rf $(VENV) rag_agent.db __pycache__ **/__pycache__ .pytest_cache

make_lint: format lint
	@echo "Lint and format complete"


