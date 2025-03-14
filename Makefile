VERSION ?= "0.1.0"


.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@echo "📦 Checking if Poetry is installed"
	@if ! command -v poetry &> /dev/null; then \
		echo "📦 Installing Poetry with pip"; \
		pip install poetry<2.0.0; \
	else \
		echo "📦 Poetry is already installed"; \
	fi
	@echo "🚀 Installing package in development mode with all extras"
	poetry install --all-extras

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@poetry run pre-commit run -a

.PHONY: set-version
set-version: ## Set the version in the pyproject.toml file
	@echo "🚀 Setting version in pyproject.toml"
	@poetry version $(VERSION)

.PHONY: unset-version
unset-version: ## Set the version in the pyproject.toml file
	@echo "🚀 Setting version in pyproject.toml"
	@poetry version 0.1.0

.PHONY: deploy
deploy: ## Deploy the app to Modal
	@echo "🚀 Deploying to Modal"
	@make clean-build
	@make build
	@modal deploy deploy.py


.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	@poetry publish --dry-run
	@echo "🚀 Publishing."
	@poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: help
help:
	@echo "🛠️ Dev Commands:\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
