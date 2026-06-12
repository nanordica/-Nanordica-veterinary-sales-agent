"""Same call via the newer Responses API — this is the shape the Azure portal
sample shows. We use API-key auth (not Entra ID) so no `az login` is needed."""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

resp = client.responses.create(
    model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.5"),
    input="What is the capital of France?",
)

print(resp.output_text)
