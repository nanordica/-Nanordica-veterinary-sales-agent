# Azure OpenAI — example calls

Ready-to-run calls against the **hackathon Azure OpenAI** models. Auth is a simple
**API key** (the organizers give it to you) — no `az login`, no cloud setup.

## Models available (deployment names)

| Use it for | Deployment name | Notes |
|---|---|---|
| General / best quality | `gpt-5.5` | Flagship reasoning model |
| Cheap & fast / high volume | `gpt-5.4-mini` | Great default for most calls |
| Embeddings (RAG, search) | `text-embedding-3-large` | Turns text into vectors |

The endpoint + deployment names are already in `../../.env.template`. Copy it to
`../../.env`, paste the **API key** from the organizers, and you're ready.

## Run it

**Python**
```bash
pip install -r requirements.txt
python chat.py          # Chat Completions (most common)
python responses.py     # Responses API (newer; what the portal shows)
python embeddings.py    # Make an embedding vector
```

**Node**
```bash
npm install openai
node --env-file=../../.env chat.mjs
```

**No SDK (raw REST)**
```bash
bash curl.sh
```

## Good to know

- **Never commit your key.** It lives in `.env`, which is gitignored. The key can
  spend the hackathon credits — treat it like a password.
- `gpt-5.x` are **reasoning models**: don't send `temperature` or `max_tokens`.
  Use `max_completion_tokens` to cap length (the examples already do).
- Want it cheaper/faster? Switch the model to `gpt-5.4-mini`.
