import logging
from logging import getLogger
from typing import Optional
from pathlib import Path

from cpr_data_access.models import Dataset, BaseDocument, Span, GSTDocument
from tqdm.auto import tqdm
import pandas as pd
from opensearchpy import helpers
import click
from dotenv import load_dotenv, find_dotenv

from src.opensearch.client import get_opensearch_client
from src.data.add_metadata import base_document_to_gst_document
from src.data.scraper import load_scraper_csv

logging.basicConfig(level=logging.INFO)
LOGGER = getLogger(__name__)


def load_spans_csv(path: Path) -> list[Span]:
    """
    Load a CSV file containing spans and return a list of Span objects.

    :param Path path: CSV file path
    :return list[Span]: list of spans
    """
    df = pd.read_csv(path)
    return [Span.parse_obj(row) for row in df.to_dict(orient="records")]


def get_dataset_with_spans(
    parser_outputs_dir: Path,
    scraper_csv_path: Path,
    concepts_dir: Path,
    limit: Optional[int] = None,
) -> Dataset:
    """
    Get a Dataset object containing spans loaded from the concepts directory.

    :param Path parser_outputs_dir: path to directory containing parsed documents
    :param Path scraper_csv_path: path to scraper CSV file
    :param Path concepts_dir: path containing subdirectories for each concept, each containing a spans.csv file
    :param Optional[int] limit: limit number of documents loaded, defaults to None
    :return Dataset: dataset object with added spans
    """
    LOGGER.info("Loading scraper CSV")
    scraper_data = load_scraper_csv(scraper_csv_path)

    LOGGER.info("Loading dataset of parsed documents")
    dataset = Dataset(BaseDocument).load_from_local(
        str(parser_outputs_dir), limit=limit
    )
    dataset.documents = [
        base_document_to_gst_document(doc, scraper_data)
        for doc in tqdm(dataset.documents)
    ]

    LOGGER.info("Adding spans")
    spans = []

    for path in concepts_dir.iterdir():
        if path.is_file():
            continue

        if not (path / "spans.csv").exists():
            print(f"failed to find spans.csv in concepts subdirectory {path}")
            continue

        concept_spans = load_spans_csv(path / "spans.csv")

        # TODO: this is to account for the fact that span types have no knowledge of their overarching concept
        # e.g. fossil fuels. Deal with this in a better way.
        concept_name = str(path).split("/")[-1]

        for span in concept_spans:
            span.type = f"{concept_name.upper()}__{span.type}"

        spans.extend(concept_spans)

    for span in spans:
        span.document_id = span.document_id.upper()

    LOGGER.info("Adding spans to dataset")
    dataset.add_spans(spans, warn_on_error=False)

    return dataset


def gst_document_to_opensearch_document(doc: GSTDocument) -> list[dict]:
    """
    Convert a GSTDocument object to a list of documents to load into OpenSearch.

    :param GSTDocument doc: GST document
    :return list[dict]: list of OpenSearch documents
    """
    if not doc.text_blocks:
        return []

    opensearch_docs = []

    for block in doc.text_blocks:
        opensearch_docs.append(
            doc.dict(exclude={"text_blocks", "page_metadata"})
            | block.dict(exclude={"text", "type"})
            | {
                "type": block.type.value,
                "text": block.to_string().replace("\n", " ").replace("  ", " "),
                "spans": [s.dict() for s in block._spans],
                "span_types": list(set([s.type for s in block._spans])),
                "span_ids": list(set([s.id for s in block._spans])),
            }
        )

    return opensearch_docs


@click.command()
@click.argument(
    "parser_outputs_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.argument(
    "scraper_csv_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "concepts_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--index", "-i", type=str, default="global-stocktake")
@click.option("--limit", "-l", type=int, default=None)
def main(parser_outputs_dir, scraper_csv_path, concepts_dir, index, limit):
    load_dotenv(find_dotenv())

    """Load dataset and index into OpenSearch."""
    opns = get_opensearch_client()

    dataset = get_dataset_with_spans(
        parser_outputs_dir, scraper_csv_path, concepts_dir, limit
    )

    LOGGER.info("Converting documents to OpenSearch documents")
    opns_docs = []
    for doc in dataset.documents:
        opns_docs.extend(gst_document_to_opensearch_document(doc))  # type: ignore

    LOGGER.info("Indexing documents")
    actions = tqdm(opns_docs, unit="docs")
    successes = 0

    for ok, _ in helpers.streaming_bulk(
        client=opns,
        index=index,
        actions=actions,
        request_timeout=60,
    ):
        successes += ok


if __name__ == "__main__":
    main()
