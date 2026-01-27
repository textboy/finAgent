import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, OrderBy
import uuid
from datetime import datetime

metadata = {"analyst_name": "reportA"}
load_dotenv(os.path.join('config', '.env'))

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

embeddings = OpenAIEmbeddings(
    model=os.getenv('EMBEDDING_MODEL_NAME'),
    openai_api_key=openrouter_api_key,
    openai_api_base=openrouter_base,
)

print(f"Using model: {embeddings.model}")

EMBED_DIM = 4096
COLL_NAME = 'finagent_reports'
symbol = "GOOG"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant")
def get_client():
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, timeout=10)
    else:
        return QdrantClient(path=QDRANT_PATH)

def init_collection():
    client = get_client()
    if client.collection_exists(COLL_NAME):
        # recreate collection
        client.delete_collection(collection_name=COLL_NAME)
    # Create the collection if it doesn't exist
    client.create_collection(
        collection_name=COLL_NAME,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )
    collection_info = client.get_collection(collection_name=COLL_NAME)

    client.create_payload_index(
        collection_name=COLL_NAME,
        field_name="analysis_datetime",
        field_schema="datetime"
    )
    print(f"Collection '{COLL_NAME}' was created")

content = "test"
try:
    emb = embeddings.embed_query(content)
    print(f"Embedding length: {len(emb)}")
    init_collection()
    point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={
                "symbol": symbol,
                "report_type": 'report',
                "content": content,
                "analysis_datetime": datetime.now(),
                "metadata": metadata or {},
            },
        )
    client = get_client()
    client.upsert(
        collection_name=COLL_NAME,
        points=[point],
    )

    # get last report
    filter_ = Filter(
        must=[
            FieldCondition(key="symbol", match=MatchValue(value=symbol)),
            FieldCondition(key="report_type", match=MatchValue(value="report")),
        ]
    )
    hits, _ = client.scroll(
        collection_name=COLL_NAME,
        scroll_filter=filter_,
        limit=1,
        with_payload=True,
        with_vectors=False,
        order_by=OrderBy(key="analysis_datetime", direction="desc"),
    )
    for hit in hits:
        print(f"Found report: {hit.payload.get('content')}")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
