.PHONY: sync frontend tool update

sync:
	uv sync

frontend:
	cd frontend && npm install && npm run build

tool:
	uv tool install --editable --reinstall .

update: sync frontend tool
