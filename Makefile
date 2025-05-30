.PHONY: install
install:
	uv pip install -r pyproject.toml --all-extras

.PHONY: run
run:
	uv run --env-file .env python3 -m main_server.main
