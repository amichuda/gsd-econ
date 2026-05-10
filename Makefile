# gsd-econ Makefile
# Common operations for development and verification.

.PHONY: help verify verify-fast verify-install lint clean install-deps

help:
	@echo "gsd-econ — common make targets"
	@echo ""
	@echo "  make verify         Run the full verification suite (pytest)"
	@echo "  make verify-fast    Run all tests except install-script tests"
	@echo "  make verify-install Run only install-script tests"
	@echo "  make lint           Run shellcheck on shell scripts (if installed)"
	@echo "  make install-deps   Install Python deps for the verification suite"
	@echo "  make clean          Remove pytest cache and other transient files"

install-deps:
	pip install -r verification/requirements.txt

verify:
	pytest verification/ -v

verify-fast:
	pytest verification/ -v --ignore=verification/test_install_script.py

verify-install:
	pytest verification/test_install_script.py -v

lint:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck scripts/*.sh; \
	else \
		echo "shellcheck not installed; skipping. (apt install shellcheck or brew install shellcheck)"; \
	fi

clean:
	rm -rf .pytest_cache verification/__pycache__ verification/.pytest_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
