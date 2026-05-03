#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"

run() {
  echo
  echo "==> $*"
  "$@"
}

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing backend virtualenv Python at $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Missing frontend/node_modules. Run 'cd frontend && npm install' first." >&2
  exit 1
fi

run "$PYTHON_BIN" -m compileall "$BACKEND_DIR" -q

(
  cd "$BACKEND_DIR"

  run "$PYTHON_BIN" -m unittest discover -s tests
  run "$PYTHON_BIN" -m unittest tests.test_eval_fixtures -v
  run "$PYTHON_BIN" -m alembic heads
  run "$PYTHON_BIN" -c "from main import app; schema=app.openapi(); print(app.title); print(sorted(schema.get('components', {}).get('schemas', {}).keys()))"
  run "$PYTHON_BIN" -c "from schemas import AGENT_LLM_RESPONSE_JSON_SCHEMA; import json; text=json.dumps(AGENT_LLM_RESPONSE_JSON_SCHEMA); assert 'default' not in text; assert 'additionalProperties' in text; print('OpenAI JSON schema OK')"

  if [[ -n "${DATABASE_URL:-}" ]]; then
    run "$PYTHON_BIN" -m alembic current
  else
    echo
    echo "==> Skipping Alembic current; set DATABASE_URL to validate the live DB revision."
  fi
)

(
  cd "$FRONTEND_DIR"

  run npm audit
  run npm run build
)

echo
echo "Validation complete."
