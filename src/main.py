from typing import Sequence

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from src.opensearch.client import get_opensearch_client

app = FastAPI()

load_dotenv(find_dotenv())


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
async def search(request: SearchRequest, opns=Depends(get_opensearch_client)):
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


@app.get("/searchFilters")
async def get_search_filters(
    index: str = "global-stocktake", opns=Depends(get_opensearch_client)
):
    """Get search filters."""
    return opns.get(index=index + "-metadata", id="filters")["_source"]
