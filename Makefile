.PHONY: seed api web test-api test-web

seed:
	cd apps/api && .venv/Scripts/python scripts/seed_database.py || .venv/bin/python scripts/seed_database.py

api:
	cd apps/api && .venv/Scripts/uvicorn app.main:app --reload --port 8000 || .venv/bin/uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test-api:
	cd apps/api && .venv/Scripts/pytest -q || .venv/bin/pytest -q

test-web:
	cd apps/web && npm run test
