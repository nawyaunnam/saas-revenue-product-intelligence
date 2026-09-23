.PHONY: setup demo test docs clean
setup:
	python3.12 -m venv .venv
	.venv/bin/pip install -e '.[dev]'
demo:
	PATH="$(CURDIR)/.venv/bin:$$PATH" saas demo
test:
	.venv/bin/ruff check src tests dags scripts
	PATH="$(CURDIR)/.venv/bin:$$PATH" pytest -q
docs:
	DUCKDB_PATH="$(CURDIR)/data/warehouse.duckdb" .venv/bin/dbt docs generate --project-dir dbt --profiles-dir dbt
