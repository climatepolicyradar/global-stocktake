import logging
from logging import getLogger
from typing import Optional
from pathlib import Path
from collections import OrderedDict
from datetime import datetime

from cpr_data_access.models import Dataset, BaseDocument, Span, GSTDocument, TextBlock
from tqdm.auto import tqdm
import pandas as pd
from opensearchpy import helpers
import click
from dotenv import load_dotenv, find_dotenv
import spacy
from bs4 import BeautifulSoup, Tag

from src.opensearch.client import get_opensearch_client
from src.opensearch.index_settings import index_settings
from src.data.add_metadata import base_document_to_gst_document
from src.data.scraper import load_scraper_csv
from src import config

logging.basicConfig(level=logging.INFO)
LOGGER = getLogger(__name__)

nlp = spacy.blank("en")  # pipeline with tokenizer only


def load_spans_csv(path: Path) -> list[Span]:
    """
    Load a CSV file containing spans and return a list of Span objects.

    :param Path path: CSV file path
    :return list[Span]: list of spans
    """
    df = pd.read_csv(path)
    return [Span.parse_obj(row) for row in df.to_dict(orient="records")]


def get_dataset_and_filter_values(
    parser_outputs_dir: Path,
    scraper_csv_path: Path,
    concepts_dir: Path,
    limit: Optional[int] = None,
) -> tuple[Dataset, dict[str, list[str]]]:
    """
    Get a Dataset object containing spans loaded from the concepts directory, and a dictionary of values to power UI filters.

    :param Path parser_outputs_dir: path to directory containing parsed documents
    :param Path scraper_csv_path: path to scraper CSV file
    :param Path concepts_dir: path containing subdirectories for each concept, each containing a spans.csv file
    :param Optional[int] limit: limit number of documents loaded, defaults to None
    :return tuple[Dataset, dict[str, list[str]]]: dataset object with added spans, dictionary of filter values
    """
    LOGGER.info("Loading scraper CSV")
    scraper_data = load_scraper_csv(scraper_csv_path)

    LOGGER.info("Loading dataset of parsed documents")
    dataset = (
        Dataset(BaseDocument)
        .load_from_local(str(parser_outputs_dir), limit=limit)
        .filter_by_language("en")
    )

    new_docs = []

    for doc in tqdm(dataset.documents):
        try:
            new_docs.append(base_document_to_gst_document(doc, scraper_data))
        except Exception as e:
            LOGGER.warning(f"Could not process document {doc.document_id}: {e}")

    LOGGER.info(
        f"Loaded {len(new_docs)} documents. {len(dataset.documents) - len(new_docs)} documents failed to load."
    )

    dataset.documents = new_docs
    dataset_metadata_df = dataset.metadata_df

    filter_values = dict()
    filter_values["dates"] = dict()
    filter_values["dates"]["date_min"] = (
        dataset_metadata_df["date"].min().strftime("%Y-%m-%d")
    )
    filter_values["dates"]["date_max"] = (
        dataset_metadata_df["date"].max().strftime("%Y-%m-%d")
    )

    filter_values["authors"] = sorted(
        dataset_metadata_df["author"].explode().unique().tolist()
    )
    filter_values["types"] = sorted(
        dataset_metadata_df["types"].explode().unique().tolist()
    )

    filter_values["concepts"] = dict()

    LOGGER.info("Loading spans from concepts directory")
    spans = []

    for path in concepts_dir.iterdir():
        if path.is_file():
            continue

        spans_files = list(path.glob("spans*.csv"))
        if len(spans_files) == 0:
            LOGGER.info(
                f"failed to find any spans.csv files in concepts subdirectory {path}"
            )
            continue

        if path.name not in config.CONCEPTS_TO_INDEX:
            LOGGER.info(
                f"Skipping concept {path.name} because it is not in config CONCEPTS_TO_INDEX"
            )
            continue

        concept_spans = []
        for spans_file in spans_files:
            concept_spans.extend(load_spans_csv(spans_file))

        # Brackets can't be used in the Makefile so "br-" and "-br" are used to represent them
        concept_name = (
            path.name.replace("br-", "(").replace("-br", ")").replace("-", " ").title()
        )

        for span in concept_spans:
            span.type = f"{concept_name} – {span.type.replace('_', ' ').title()}"

        spans.extend(concept_spans)

        # NOTE: the logic to add the "Concept – All" filter value is in the gst_document_to_opensearch_document function too.
        filter_values["concepts"][concept_name] = [f"{concept_name} – All"] + sorted(
            list(set([span.type for span in concept_spans]))
        )

        # Use 'annotator' property of spans to store whether the concept is a full-passage concept or not
        if path.name in config.FULL_PASSAGE_CONCEPTS:
            for span in concept_spans:
                span.annotator = "full_passage"
        elif path.name in config.PARTIAL_PASSAGE_CONCEPTS_TO_INDEX:
            for span in concept_spans:
                span.annotator = "partial_passage"
        else:
            raise ValueError(
                f"Concept {path.name} not found in config. This means there's likely a bug in the indexing code."
            )

    filter_values["concepts"] = OrderedDict(sorted(filter_values["concepts"].items()))

    LOGGER.info("Adding spans to dataset")
    dataset.add_spans(spans, warn_on_error=False)

    return dataset, filter_values


def fix_text_block_string(block_str: str) -> str:
    """
    Perform some text cleanup on a text block string for the UI.

    Eventually this should probably live in the data access library but modifying the TextBlock.to_string() method breaks hash checking with
    already saved spans.
    """

    return (
        block_str.replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
        .replace("  ", " ")
    )


def text_block_to_html(block: TextBlock) -> str:
    """
    Convert a text block to HTML for the retool UI.

    This uses displacy to generate the HTML, and then adds HTML classes and IDs to allow it to be styled.

    :param TextBlock block: text block
    :return str: html for display
    """

    block_for_display = block.copy()
    block_for_display._spans = [
        span for span in block._spans if span.annotator != "full_passage"
    ]

    block_html = block_for_display.display(style="span", nlp=nlp).replace("</br>", " ")
    soup = BeautifulSoup(block_html, "html.parser")

    def label_text_to_spans(text: str) -> tuple[Tag, Tag]:
        """Convert label text e.g. 'Greenhouse Gases – Oil' to two HTML spans."""

        concept, subconcept = [i.strip() for i in text.strip().split("–")]

        concept_span = soup.new_tag("span")
        concept_span.attrs["class"] = "concept-label"
        concept_span.string = concept + " – "

        subconcept_span = soup.new_tag("span")
        subconcept_span.attrs["class"] = "subconcept-label"
        subconcept_span.string = subconcept

        return concept_span, subconcept_span

    for span in soup.find_all("span", {"style": lambda x: "z-index: 10" in x}):
        span.attrs["class"] = "span-label"
        span.attrs["id"] = span.text.strip()
        span.parent.parent.attrs["class"] = (
            "text-highlight" + " " + span.text.strip().replace(" ", "-")
        )

        concept_span, subconcept_span = label_text_to_spans(span.text)
        span.string.replace_with("")
        span.append(concept_span)
        span.append(subconcept_span)

    return soup.prettify()


def gst_document_to_opensearch_document(doc: GSTDocument) -> list[dict]:
    """
    Convert a GSTDocument object to a list of documents to load into OpenSearch.

    :param GSTDocument doc: GST document
    :return list[dict]: list of OpenSearch documents
    """
    if not doc.text_blocks:
        return []

    opensearch_docs = []
    doc_dict = doc.dict(
        exclude={"text_blocks", "page_metadata", "_text_block_idx_hash_map"}
    )

    for idx, block in enumerate(doc.text_blocks):
        block_before_text = "" if idx == 0 else doc.text_blocks[idx - 1].to_string()

        block_after_text = (
            ""
            if idx == len(doc.text_blocks) - 1
            else doc.text_blocks[idx + 1].to_string()
        )

        span_types = list(set([s.type for s in block._spans]))
        span_types_full_passage = list(
            set([s.type for s in block._spans if s.annotator == "full_passage"])
        )

        # For each all span types that the block contains, add a generic "Concept – All" value
        span_types.extend(list(set([s.split(" – ")[0] + " – All" for s in span_types])))
        span_types_full_passage.extend(
            list(set([s.split(" – ")[0] + " – All" for s in span_types_full_passage]))
        )

        opensearch_docs.append(
            doc_dict
            | block.dict(
                exclude={
                    "text",
                    "type",
                }
            )
            | {
                "type": block.type.value,
                "text_before": fix_text_block_string(block_before_text),
                "text": fix_text_block_string(block.to_string()),
                "text_after": fix_text_block_string(block_after_text),
                "text_html": text_block_to_html(block),
                "spans": [s.dict() for s in block._spans],
                "span_types": span_types,
                "span_types_full_passage": span_types_full_passage,
                "span_ids": list(set([s.id for s in block._spans])),
                "is_party": doc.document_metadata.author_is_party,
                "date_string": doc.document_metadata.date.strftime("%Y-%m-%d")
                if doc.document_metadata.date
                else None,
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
@click.option("--index-prefix", "-i", type=str, default="global-stocktake")
@click.option("--limit", "-l", type=int, default=None)
def main(parser_outputs_dir, scraper_csv_path, concepts_dir, index_prefix, limit):
    load_dotenv(find_dotenv())

    timestr = datetime.now().strftime("%Y%m%d-%H%M%S")
    index_name = f"{index_prefix}-{timestr}"

    """Load dataset and index into OpenSearch."""
    opns = get_opensearch_client()

    LOGGER.info(f"Creating index {index_name}")
    opns.indices.create(index=index_name, body=index_settings)

    dataset, filter_values = get_dataset_and_filter_values(
        parser_outputs_dir, scraper_csv_path, concepts_dir, limit
    )

    LOGGER.info("Converting documents to OpenSearch documents")
    opns_docs = []
    for doc in tqdm(dataset.documents):
        opns_docs.extend(gst_document_to_opensearch_document(doc))  # type: ignore

    LOGGER.info("Indexing documents")
    actions = tqdm(opns_docs, unit="docs")
    successes = 0

    for ok, _ in helpers.streaming_bulk(
        client=opns,
        index=index_name,
        actions=actions,
        request_timeout=60,
        max_retries=5,
    ):
        successes += ok

    LOGGER.info(f"Indexing metadata to index {index_name+'-metadata'}")
    opns.index(index=index_name + "-metadata", body=filter_values, id="filters")

    LOGGER.info(f"New index names: {index_name}, {index_name+'-metadata'}")


if __name__ == "__main__":
    main()
