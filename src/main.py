from typing import Sequence, Optional
import itertools

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
    is_party: Optional[bool] = None
    index: str = "global-stocktake"
    limit: int = 10
    offset: int = 0


@app.post("/search")
async def search(request: SearchRequest, opns=Depends(get_opensearch_client)):
    """Get search results."""

    query_body = {
        "from": request.offset,
        "size": request.limit,
        "query": {
            "bool": {
                "must": [],
            }
        },
    }

    if request.text:
        query_body["query"]["bool"]["must"].append(
            {"match": {"text_html": {"query": request.text, "operator": "and"}}}
        )

        query_body["highlight"] = {
            "number_of_fragments": 0,
            "fields": {
                "text_html": {
                    "pre_tags": [
                        '<mark class="entity" style="background: #fbec5d; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">'
                    ],
                    "post_tags": ["</mark>"],
                },
            },
        }

    else:
        query_body["query"]["bool"]["must"].append({"match_all": {}})

    if request.span_types or request.is_party is not None:
        query_body["query"]["bool"].update({"filter": []})

    if request.span_types:
        # Create an OR filter for types within the same concept, and an AND filter between concepts.
        # E.g. (Fossil fuels - Coal OR Fossil fuels - Oil) AND (Energy - Electricity)
        types_with_concepts = sorted(
            [(type.split("–")[0].strip(), type) for type in request.span_types]
        )

        for _, types_with_concepts_group in itertools.groupby(
            types_with_concepts, lambda x: x[0]
        ):
            types = [type[1] for type in types_with_concepts_group]
            query_body["query"]["bool"]["filter"].append(
                {"terms": {"span_types": types}}
            )

    if request.is_party is not None:
        query_body["query"]["bool"]["filter"].append(
            {"term": {"is_party": request.is_party}}
        )

    opns_result = opns.search(index=request.index, body=query_body)

    if not request.text:
        for item in opns_result["hits"]["hits"]:
            item["highlight"] = {}
            item["highlight"]["text_html"] = [item["_source"]["text_html"]]

    return opns_result


@app.get("/searchFilters")
async def get_search_filters(
    index: str = "global-stocktake", opns=Depends(get_opensearch_client)
):
    """Get search filters."""
    return opns.get(index=index + "-metadata", id="filters")["_source"]
