#!/usr/bin/env bash
# Run the live golden-path e2e for both adapters (claude + codex).
#
# Needs a local llm-gateway (run `./bin/start` in the posthog repo) and a token.
# The suite targets the gateway's `ci` product, which accepts a personal
# API key (no OAuth). Set POSTHOG_CODE_E2E_GATEWAY_PERSONAL_API_KEY to a key registered in the local DB.
#
# Usage:
#   bash e2e/run-e2e.sh              # both adapters, both suites
#   bash e2e/run-e2e.sh -t "(codex)" # only the codex arm (vitest -t name filter)
# Env overrides: POSTHOG_CODE_E2E_GATEWAY_URL, POSTHOG_CODE_E2E_CLAUDE_MODEL, POSTHOG_CODE_E2E_CODEX_MODEL, E2E_DEBUG=1
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(cd "$HERE/.." && pwd)"

if [[ -z "${POSTHOG_CODE_E2E_GATEWAY_PERSONAL_API_KEY:-}" ]]; then
  echo "POSTHOG_CODE_E2E_GATEWAY_PERSONAL_API_KEY is unset. Set it to a personal API key registered in the local DB." >&2
  exit 1
fi

export POSTHOG_CODE_E2E_GATEWAY_PERSONAL_API_KEY
echo "token: ${POSTHOG_CODE_E2E_GATEWAY_PERSONAL_API_KEY:0:8}…  gateway: ${POSTHOG_CODE_E2E_GATEWAY_URL:-http://localhost:3308/ci}"
cd "$AGENT_DIR"
pnpm test:e2e "$@"
