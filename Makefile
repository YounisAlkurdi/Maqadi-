.PHONY: run test lint format

run:
	cd backend && uvicorn app.main:app --reload

test:
	cd backend && pytest

lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff format .
