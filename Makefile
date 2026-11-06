PORT ?= 8000

.DEFAULT_GOAL := help
.PHONY: help install build serve publish check clean

help:
	@echo "Targets:"
	@echo "  make install   Create .venv and install dependencies"
	@echo "  make build     Build the site into output/ (development settings)"
	@echo "  make serve     Build, serve and auto-reload at http://localhost:$(PORT)"
	@echo "  make publish   Build with production settings into output/"
	@echo "  make check     Build, then check links, pages and counts in output/"
	@echo "  make clean     Remove output/ and cache/"

install:
	uv sync

build:
	uv run pelican content -s pelicanconf.py

serve:
	uv run pelican content -s pelicanconf.py --autoreload --listen --port $(PORT)

publish:
	uv run pelican content -s publishconf.py

check: build
	uv run python scripts/check_site.py

clean:
	rm -rf output cache
