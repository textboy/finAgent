import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv(os.path.join('config', '.env'))

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

embeddings = OpenAIEmbeddings(
    model=os.getenv('EMBEDDING_MODEL_NAME'),
    openai_api_key=openrouter_api_key,
    openai_api_base=openrouter_base,
)

print(f"Using model: {embeddings.model}")

try:
    emb = embeddings.embed_query("test")
    print(f"Embedding length: {len(emb)}")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
