#!/usr/bin/env bash
# Run all tests for the Threat Detection System (engine, agent).
# Optional: use existing .venv or create one; otherwise uses current Python.

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Use .venv if present
if [ -d ".venv" ]; then
  PYTHON="${ROOT}/.venv/bin/python"
  PIP="${ROOT}/.venv/bin/pip"
  PYTEST="${ROOT}/.venv/bin/pytest"
else
  PYTHON="${PYTHON:-python3}"
  PIP="$PYTHON -m pip"
  PYTEST="$PYTHON -m pytest"
fi

export PYTHONPATH="$ROOT"

echo "=== Threat Detection System — Test Runner ==="
echo "Python: $PYTHON"
echo ""

# Ensure pytest is available (install in venv or suggest install)
if ! $PYTEST --version &>/dev/null; then
  echo "Installing test dependencies..."
  $PIP install -q pytest pytest-cov
  $PIP install -q -r engine/requirements.txt
  $PIP install -q -r agent/requirements.txt
fi

# Engine tests (use in-memory SQLite via ENGINE_DATABASE_URL)
echo "--- Engine tests ---"
export ENGINE_DATABASE_URL="${ENGINE_DATABASE_URL:-sqlite:///:memory:}"
$PYTEST engine/tests -v --tb=short
ENGINE_EXIT=$?

# Agent tests
echo ""
echo "--- Agent tests ---"
$PYTEST agent/tests -v --tb=short
AGENT_EXIT=$?

# Dashboard: run lint if available (no test script in package.json by default)
echo ""
echo "--- Dashboard (lint only) ---"
if [ -f "dashboard/package.json" ] && grep -q '"lint"' dashboard/package.json; then
  (cd dashboard && npm run lint 2>/dev/null) || true
fi

echo ""
if [ "$ENGINE_EXIT" -eq 0 ] && [ "$AGENT_EXIT" -eq 0 ]; then
  echo "All component tests passed."
  exit 0
else
  echo "Some tests failed (engine: $ENGINE_EXIT, agent: $AGENT_EXIT)."
  exit 1
fi
