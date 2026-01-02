import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, List, Optional
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, OrderBy
from langchain_openai import OpenAIEmbeddings

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    openai_api_key=openrouter_api_key,
    openai_api_base=openrouter_base,
)

EMBED_DIM = 1536

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant")
COLL_NAME = os.getenv("MILVUS_COLL_NAME", "finagent_reports")  # reuse name
def get_client():
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL)
    else:
        return QdrantClient(path=QDRANT_PATH)

def init_collection():
    client = get_client()
    client.recreate_collection(
        collection_name=COLL_NAME,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.EUCLID),
    )

def store_entry(symbol: str, report_type: str, content: str, analysis_datetime: str, metadata: Dict[str, Any] = None):
    init_collection()
    emb = embeddings.embed_query(content)
    point = models.PointStruct(
        id=models.GenerateId(),
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
    results = client.scroll(
        collection_name=COLL_NAME,
        scroll_filter=filter_,
        limit=1,
        with_payload=True,
        with_vectors=False,
        order_by=OrderBy(key="analysis_datetime", desc=True),
    )
    hits, _ = results
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
    results = client.scroll(
        collection_name=COLL_NAME,
        scroll_filter=filter_,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )
    hits, _ = results
    return [hit.payload["content"] for hit in hits]