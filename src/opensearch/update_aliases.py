import logging
from logging import getLogger

import click
from dotenv import load_dotenv, find_dotenv

from src.opensearch.client import get_opensearch_client

logging.basicConfig(level=logging.INFO)
LOGGER = getLogger(__name__)


@click.command()
@click.argument("new_index_prefix")
def update_aliases(new_index_prefix: str):
    """
    Update indices which point to the global-stocktake-docs and global-stocktake-docs-metadata aliases.

    :param str new_index_prefix: the new index prefix to point to the aliases. E.g. "global-stocktake-20230525-112054"
    """
    load_dotenv(find_dotenv(), override=True)
    opns = get_opensearch_client()

    body = {
        "actions": [
            {
                "remove": {
                    "index": "global-stocktake*",
                    "alias": "global-stocktake-docs",
                }
            },
            {"add": {"index": new_index_prefix, "alias": "global-stocktake-docs"}},
            {
                "remove": {
                    "index": "global-stocktake*",
                    "alias": "global-stocktake-docs-metadata",
                }
            },
            {
                "add": {
                    "index": f"{new_index_prefix}-metadata",
                    "alias": "global-stocktake-docs",
                }
            },
        ]
    }

    opns.indices.update_aliases(body=body)

    LOGGER.info(f"Updated aliases to point to {new_index_prefix}")


if __name__ == "__main__":
    update_aliases()
