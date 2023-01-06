.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  init       Install for development (includes tox and pre-commit)"

.PHONY: init
init:
	pip install -e ".[aiohttp,httpx,dev]"
	pip install tox pre-commit
	pre-commit install
	rm -rf .tox
