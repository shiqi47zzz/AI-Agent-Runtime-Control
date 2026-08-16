.PHONY: install run test lint

install:
	python -m pip install -e '.[dev]'

run:
	uvicorn agent_api_guard.app:app --reload --host 0.0.0.0 --port 8080

test:
	pytest

lint:
	ruff check .
