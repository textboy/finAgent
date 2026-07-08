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

# Get embedding API key - use FINAGENT_ZENMUX_API_KEY for embeddings
embedding_api_key = os.getenv("FINAGENT_ZENMUX_API_KEY") or os.getenv("ZENMUX_API_KEY")
embedding_base = os.getenv("LLM_BASE_URL", "https://zenmux.ai/api/v1")
COLL_NAME = 'finagent_reports'

# Only initialize embeddings if API key is available
embeddings = None
if embedding_api_key:
    try:
        embeddings = OpenAIEmbeddings(
            model=os.getenv('EMBEDDING_MODEL_NAME', DEFAULT_EMBEDDING_MODEL_NAME),
            openai_api_key=embedding_api_key,
            openai_api_base=embedding_base,
        )
    except Exception as e:
        print(f"WARNING: Could not initialize embeddings: {e}")

EMBED_DIM = 4096

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant")
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
qrant_server_health_status = False

# Qdrant is optional for testing - will bypass memory if not available
try:
    response = requests.get(f"{QDRANT_URL}/health", timeout=5)
    if response.status_code == 200:
        qrant_server_health_status = True
    else:
        print("WARNING: Qdrant server is not started, bypassing memory processing.")
except Exception as e:
    print("WARNING: Qdrant server is not started, bypassing memory processing.")

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
    """Store an entry in Qdrant with embedding for semantic search."""
    if not qrant_server_health_status:
        return
    if not embeddings:
        print("WARNING: Embeddings not available, skipping store_entry")
        return
    init_collection()
    if content:
        print(f'DEBUG: store_entry content-{content[:100]}...')
        try:
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
        except Exception as e:
            print(f"WARNING: Failed to store entry: {e}")

def get_last_report(symbol: str) -> Optional[Dict[str, Any]]:
    """Get the most recent report for a symbol from Qdrant."""
    if not qrant_server_health_status:
        return None
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
    """Get past lessons learned for a symbol from Qdrant."""
    if not qrant_server_health_status:
        return []
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
