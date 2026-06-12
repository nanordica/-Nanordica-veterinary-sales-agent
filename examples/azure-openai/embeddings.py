"""Turn text into a vector — the building block for RAG / semantic search."""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

resp = client.embeddings.create(
    model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
    input="Ribosomes translate mRNA into protein.",
)

vec = resp.data[0].embedding
print(f"Got a {len(vec)}-dimensional vector. First 5 numbers: {vec[:5]}")
