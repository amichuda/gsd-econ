#!/usr/bin/env bash
# CLI test runner — invokes /gsd-test-paper via the runtime in non-interactive mode.
# Usage:
#   bash vendor/gsd-econ/scripts/run-tests.sh [--methodology did] [--severity blocker]
#
# Requires: an installed runtime (claude or opencode) with gsd-econ commands available.

set -euo pipefail

ARGS="$*"

# Detect runtime
if command -v claude >/dev/null 2>&1; then
    RUNTIME_CMD="claude"
elif command -v opencode >/dev/null 2>&1; then
    RUNTIME_CMD="opencode"
else
    echo "ERROR: neither 'claude' nor 'opencode' found in PATH."
    echo "Install the relevant runtime first."
    exit 1
fi

echo "→ Using runtime: $RUNTIME_CMD"
echo "→ Running gsd-test-paper with args: $ARGS"
echo

# Most runtimes support a non-interactive '-p' or '--prompt' flag.
# Adjust below if your runtime differs.

if [[ "$RUNTIME_CMD" == "claude" ]]; then
    claude -p "/gsd-test-paper $ARGS"
else
    # opencode
    opencode run "/gsd-test-paper $ARGS"
fi

# Output is in .planning/test-runs/<ISO>-test-paper.{md,jsonl}
LATEST=$(find .planning/test-runs -name "*-test-paper.md" -printf "%T@ %p\n" 2>/dev/null \
         | sort -rn | head -n1 | cut -d' ' -f2-)

echo
if [[ -n "$LATEST" ]]; then
    echo "→ Report: $LATEST"
    echo
    # Print just the summary section
    awk '/^## Phase verdict/,/^---$/' "$LATEST" 2>/dev/null || head -40 "$LATEST"
else
    echo "⚠ No test report found in .planning/test-runs/."
    echo "  Check the runtime output above for errors."
fi
