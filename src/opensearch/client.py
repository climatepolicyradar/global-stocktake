import os

from opensearchpy import OpenSearch


def get_opensearch_client() -> OpenSearch:
    client = OpenSearch(
        [os.environ["OPENSEARCH_HOST"]],
        http_auth=(
            os.environ["OPENSEARCH_USERNAME"],
            os.environ["OPENSEARCH_PASSWORD"],
        ),
        use_ssl=True,
        verify_certs=True,
        ssl_show_warn=True,
    )

    if not client.ping():
        raise RuntimeError("Connection failed")

    return client
