# gsd-econ Makefile
# Common operations for development and verification.
#
# By default, this Makefile uses `uv` (https://docs.astral.sh/uv/) which
# is faster, manages a project-scoped venv automatically, and reads
# dependencies from pyproject.toml.
#
# If you don't have uv, the Makefile falls back to system pip/pytest.
# Install uv with:
#   curl -LsSf https://astral.sh/uv/install.sh | sh
# or:
#   brew install uv
# or:
#   pipx install uv

.PHONY: help verify verify-fast verify-install lint clean install-deps check-runner sync

# Detect uv; fall back to plain pip + python3 if missing.
UV := $(shell command -v uv 2>/dev/null)
PYTHON ?= python3
PIP ?= pip3

ifeq ($(UV),)
    # No uv — use system python directly.
    RUNNER := $(PYTHON) -m
    PYTEST := $(RUNNER) pytest
    HAVE_UV := no
else
    # uv available — use `uv run --group dev` which auto-installs deps from pyproject.toml.
    RUNNER := uv run --group dev
    PYTEST := $(RUNNER) pytest
    HAVE_UV := yes
endif

help:
	@echo "gsd-econ — common make targets"
	@echo ""
	@echo "  make verify         Run the full verification suite (pytest)"
	@echo "  make verify-fast    Run all tests except install-script tests"
	@echo "  make verify-install Run only install-script tests"
	@echo "  make sync           Sync dev dependencies (uv only)"
	@echo "  make install-deps   Install Python deps for the verification suite"
	@echo "  make lint           Run shellcheck on shell scripts (if installed)"
	@echo "  make clean          Remove pytest cache and other transient files"
	@echo ""
ifeq ($(HAVE_UV),yes)
	@echo "Using uv ($(shell uv --version)). Deps managed via pyproject.toml."
else
	@echo "uv not detected — falling back to '$(PYTHON) -m pytest'."
	@echo "For a faster, isolated workflow, install uv:"
	@echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
endif

# Synchronize dev dependencies. Cheap and idempotent under uv; uv creates
# .venv if needed and installs from pyproject.toml's [dependency-groups] dev.
sync:
ifeq ($(HAVE_UV),yes)
	uv sync --group dev
else
	@echo "sync is a uv-only target; for plain pip use 'make install-deps'."
	@exit 1
endif

# install-deps works in both modes.
install-deps:
ifeq ($(HAVE_UV),yes)
	uv sync --group dev
else
	@if [ -f verification/requirements.txt ]; then \
		$(PIP) install -r verification/requirements.txt || \
		$(PIP) install --user -r verification/requirements.txt || \
		$(PIP) install --break-system-packages -r verification/requirements.txt; \
	else \
		$(PIP) install pytest pyyaml || \
		$(PIP) install --user pytest pyyaml || \
		$(PIP) install --break-system-packages pytest pyyaml; \
	fi
	@echo ""
	@echo "Optional: install cffconvert for formal CITATION.cff schema validation:"
	@echo "  $(PIP) install cffconvert"
endif

# Sanity check that pytest is reachable before the test targets run.
# Under uv this is a no-op (uv run handles it). Under pip, it surfaces
# a useful error if pytest isn't installed.
check-runner:
ifneq ($(HAVE_UV),yes)
	@$(PYTHON) -c "import pytest" 2>/dev/null || { \
		echo "Error: pytest is not installed for $(PYTHON)."; \
		echo "Try: make install-deps"; \
		echo "Or install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	}
endif

verify: check-runner
	$(PYTEST) verification/ -v

verify-fast: check-runner
	$(PYTEST) verification/ -v --ignore=verification/test_install_script.py

verify-install: check-runner
	$(PYTEST) verification/test_install_script.py -v

lint:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck install.sh scripts/*.sh; \
	else \
		echo "shellcheck not installed; skipping. (apt install shellcheck or brew install shellcheck)"; \
	fi

clean:
	rm -rf .pytest_cache verification/__pycache__ verification/.pytest_cache .venv
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
