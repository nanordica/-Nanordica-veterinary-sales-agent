"""Your first Azure OpenAI call — chat (the familiar Chat Completions API).

Setup (from this folder):
    pip install -r requirements.txt
    # then put the API key the organizers gave you into the repo's .env file:
    #   cp ../../.env.template ../../.env   and paste the key into AZURE_OPENAI_API_KEY
    python chat.py
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # finds the repo-root .env automatically

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],  # ends with /openai/v1/  (no api-version needed)
    api_key=os.environ["AZURE_OPENAI_API_KEY"],    # the key from the organizers
)

resp = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.5"),  # a *deployment* name
    messages=[
        {"role": "system", "content": "You are a helpful hackathon assistant."},
        {"role": "user", "content": "In one sentence, what is a bioprotocol?"},
    ],
    # NOTE: gpt-5.x are reasoning models — do NOT pass temperature or max_tokens.
    # Use max_completion_tokens to cap length (leave room for reasoning + answer).
    max_completion_tokens=2000,
)

print(resp.choices[0].message.content)
