.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  init       Install for development (includes tox and pre-commit)"

.PHONY: init
init:
	pip install -e ".[aiohttp,httpx,pydantic,aiokafka,dev]"
	pip install -U tox pre-commit scriv
	pre-commit install
	rm -rf .tox
