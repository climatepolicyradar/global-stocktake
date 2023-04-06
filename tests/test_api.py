from fastapi.testclient import TestClient
from openmock.fake_opensearch import FakeOpenSearch

from src.main import app
from src.opensearch.client import get_opensearch_client


def get_fake_opensearch():
    fake_opns = FakeOpenSearch()
    fake_opns.indices.create("global-stocktake")
    fake_opns.indices.create("global-stocktake-metadata")
    fake_opns.index(
        index="global-stocktake-metadata", id="filters", body={"filters": []}
    )
    return fake_opns


client = TestClient(app)
app.dependency_overrides[get_opensearch_client] = get_fake_opensearch


def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_search():
    response = client.post("/search", json={"text": "test", "span_types": ["test"]})

    assert response.status_code == 200


def test_get_search_filters():
    response = client.get("/searchFilters")

    assert response.status_code == 200
