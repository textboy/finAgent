import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, List, Optional
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, OrderBy
from langchain_openai import OpenAIEmbeddings
import uuid

DEFAULT_EMBEDDING_MODEL_NAME = 'qwen/qwen3-embedding-8b'
load_dotenv(os.path.join('config', '.env'))
print(f'Qdrant URL: {os.getenv("QDRANT_URL")}')

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
COLL_NAME = 'finagent_reports'

embeddings = OpenAIEmbeddings(
    model=os.getenv('EMBEDDING_MODEL_NAME', DEFAULT_EMBEDDING_MODEL_NAME),
    openai_api_key=openrouter_api_key,
    openai_api_base=openrouter_base,
)

EMBED_DIM = 4096

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant")

try:
    response = requests.get(f"{QDRANT_URL}/collections/")
    print("Server response:", response.json())
except Exception as e:
    print("Failed to connect to Qdrant:", str(e))

def get_client():
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, timeout=10)
    else:
        return QdrantClient(path=QDRANT_PATH)

def init_collection():
    client = get_client()
    if not client.collection_exists(COLL_NAME):
        # Create the collection if it doesn't exist
        client.create_collection(
            collection_name=COLL_NAME,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
        client.create_payload_index(
            collection_name=COLL_NAME,
            field_name="analysis_datetime",
            field_schema="datetime"
        )
    else:
        print(f"Collection '{COLL_NAME}' already exists.")

def store_entry(symbol: str, report_type: str, content: str, analysis_datetime: str, metadata: Dict[str, Any] = None):
    init_collection()
    if content:
        print(f'DEBUG: store_entry content-{content}')
        emb = embeddings.embed_query(content)
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={
                "symbol": symbol,
                "report_type": report_type,
                "content": content,
                "analysis_datetime": analysis_datetime,
                "metadata": metadata or {},
            },
        )
        client = get_client()
        client.upsert(
            collection_name=COLL_NAME,
            points=[point],
        )

def get_last_report(symbol: str) -> Optional[Dict[str, Any]]:
    init_collection()
    filter_ = Filter(
        must=[
            FieldCondition(key="symbol", match=MatchValue(value=symbol)),
            FieldCondition(key="report_type", match=MatchValue(value="report")),
        ]
    )
    client = get_client()
    hits, _ = client.scroll(
        collection_name=COLL_NAME,
        scroll_filter=filter_,
        limit=1,
        with_payload=True,
        with_vectors=False,
        order_by=OrderBy(key="analysis_datetime", direction="desc"),
    )
    if hits:
        payload = dict(hits[0].payload)
        payload["id"] = hits[0].id
        return payload
    return None

def get_past_lessons(symbol: str) -> List[str]:
    init_collection()
    filter_ = Filter(
        must=[
            FieldCondition(key="symbol", match=MatchValue(value=symbol)),
            FieldCondition(key="report_type", match=MatchValue(value="lesson")),
        ]
    )
    client = get_client()
    hits, _ = client.scroll(
        collection_name=COLL_NAME,
        scroll_filter=filter_,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )
    return [hit.payload["content"] for hit in hits]
