#!/usr/bin/env bash
# Raw REST call — no SDK. Loads the repo-root .env, then hits the chat endpoint.
set -euo pipefail
set -a; source "$(git rev-parse --show-toplevel)/.env"; set +a

curl -sS "${AZURE_OPENAI_ENDPOINT%/}/chat/completions" \
  -H "Authorization: Bearer ${AZURE_OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
        \"model\": \"${AZURE_OPENAI_CHAT_DEPLOYMENT:-gpt-5.5}\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Hello from curl\"}],
        \"max_completion_tokens\": 2000
      }"
echo
