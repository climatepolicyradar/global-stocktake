from typing import Sequence

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from src.opensearch.client import get_opensearch_client

app = FastAPI()

load_dotenv(find_dotenv())
opns = get_opensearch_client()


@app.get("/health")
async def get_health():
    """
    Get application health.

    TODO: fill in implementation with real health check.
    """
    return {"status": "OK"}


class SearchRequest(BaseModel):
    """Request body for search endpoint."""

    text: str
    span_types: Sequence[str] = []
    index: str = "global-stocktake"
    limit: int = 100


@app.post("/search")
async def search(request: SearchRequest):
    """Get search results."""

    query_body = {
        "query": {
            "bool": {
                "must": [{"match": {"text": request.text}}],
            }
        }
    }

    if request.span_types:
        query_body["query"]["bool"].update(
            {"filter": [{"terms": {"span_types": request.span_types}}]}  # type: ignore
        )

    return opns.search(index=request.index, body=query_body)
