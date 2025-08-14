PYTHON=python3
VENV=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

.PHONY: venv install run dev lint format test clean make_lint

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -e .

run:
	$(PY) app.py

dev:
	FLASK_APP=app.py $(PY) -m flask run --debug

lint:
	$(VENV)/bin/ruff check .

format:
	$(VENV)/bin/black .

test:
	$(PY) -m pytest -q || true

clean:
	rm -rf $(VENV) rag_agent.db __pycache__ **/__pycache__ .pytest_cache

make_lint: format lint
	@echo "Lint and format complete"


