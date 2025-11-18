PY=uv run python
UV=uv

.PHONY: setup sync run dev lint format type test hooks hooks-strict hooks-update clean db-up db-down db-restart db-logs db-backup db-restore db-migrate db-reset

setup:
	$(UV) sync
	$(UV) run pre-commit install

sync:
	$(UV) sync

run:
	$(UV) run uvicorn app.main:app --host 0.0.0.0 --port 2003 --reload

dev: run

lint:
	$(UV) run ruff check app tests
	$(UV) run black --check .
	$(UV) run isort --check-only .

format:
	$(UV) run ruff check app tests --fix
	$(UV) run ruff format .
	$(UV) run isort .

type:
	$(UV) run mypy app

test:
	$(UV) run pytest

# Auto-fix formatting (lenient mode)
hooks:
	$(UV) run pre-commit run --all-files

# Strict checking (mypy, bandit, etc.)
hooks-strict:
	./scripts/check-strict.sh

hooks-update:
	$(UV) run pre-commit autoupdate
	$(UV) add --dev --upgrade pre-commit

clean:
	find . -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache

# Database commands
db-up:
	docker-compose -f docker-compose.postgres.yml up -d
	@echo "Waiting for database to be ready..."
	@sleep 3
	@docker exec vietmindai-postgres pg_isready -U mindai_user -d mindai_adk || (echo "Database not ready. Check logs with 'make db-logs'" && exit 1)
	@echo "Database is ready!"

db-down:
	docker-compose -f docker-compose.postgres.yml down

db-restart:
	docker-compose -f docker-compose.postgres.yml restart

db-logs:
	docker-compose -f docker-compose.postgres.yml logs -f postgres

db-backup:
	@mkdir -p docker/postgres/backups
	docker exec vietmindai-postgres pg_dump -U mindai_user mindai_adk | gzip > docker/postgres/backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup created in docker/postgres/backups/"

db-restore:
	@echo "Restoring from most recent backup..."
	@gunzip -c $$(ls -t docker/postgres/backups/*.sql.gz | head -1) | docker exec -i vietmindai-postgres psql -U mindai_user -d mindai_adk
	@echo "Restore complete!"

db-migrate:
	$(UV) run alembic upgrade head

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.postgres.yml down -v && \
		docker-compose -f docker-compose.postgres.yml up -d && \
		sleep 5 && \
		$(UV) run alembic upgrade head && \
		echo "Database reset complete!"; \
	fi
