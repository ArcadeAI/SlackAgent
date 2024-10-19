VERSION ?= "0.1.0.dev0"

.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@cd archer && poetry install --all-extras
	@cd archer && poetry run pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@cd archer && poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@cd archer && poetry run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@cd archer && poetry run mypy $(git ls-files '*.py')

.PHONY: set-version
set-version: ## Set the version in the pyproject.toml file
	@echo "🚀 Setting version in pyproject.toml"
	@cd archer && poetry version $(VERSION)

.PHONY: unset-version
unset-version: ## Set the version in the pyproject.toml file
	@echo "🚀 Setting version in pyproject.toml"
	@cd archer && poetry version 0.1.0

.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@cd archer && poetry build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@cd archer && rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@cd archer && poetry config pypi-token.pypi $(PYPI_TOKEN)
	@cd archer && poetry publish --dry-run
	@echo "🚀 Publishing."
	@cd archer && poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: help
help:
	@echo "🛠️ Dev Commands:\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
