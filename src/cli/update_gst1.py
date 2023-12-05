"""
Automate some of the tasks related to updating gst1.org.

Tasks:
1. checking for new documents in the new CSV
2. finding the corresponding parser outputs in S3
3. downloading the parser output JSONs to a local directory
"""

from pathlib import Path
from typing import Optional
import logging
import os
import json

from cloudpathlib import S3Path
import pandas as pd
from tqdm.auto import tqdm
from rich.logging import RichHandler
from dotenv import load_dotenv, find_dotenv
import click


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(RichHandler(rich_tracebacks=True))


def get_new_document_ids_from_csv(old_csv_path: Path, new_csv_path: Path) -> list[str]:
    """Return document IDs of new documents."""

    doc_id_col = "CPR Document ID"

    old_df = pd.read_csv(old_csv_path)
    old_df = old_df.dropna(subset=[doc_id_col])

    new_df = pd.read_csv(new_csv_path)
    new_df = new_df.dropna(subset=[doc_id_col])

    new_ids = list(set(new_df[doc_id_col]) - set(old_df[doc_id_col]))

    return new_ids


def get_parser_outputs_from_s3(
    s3_dir: S3Path, doc_ids: list[str]
) -> dict[str, Optional[str]]:
    """Return parser output JSONs that exist in S3. Prioritises translated versions over original language versions."""

    s3_doc_ids = dict()
    doc_id_json_map = dict()

    LOGGER.info("Checking for parser outputs in S3...")
    for doc_id in tqdm(doc_ids):
        if (s3_dir / f"{doc_id}_translated_en.json").exists():
            s3_doc_ids[doc_id] = f"{doc_id}_translated_en.json"

        elif (s3_dir / f"{doc_id}.json").exists():
            s3_doc_ids[doc_id] = f"{doc_id}.json"

        else:
            s3_doc_ids[doc_id] = None

    _n = "\n"
    docs_found = [
        doc_id for doc_id, filename in s3_doc_ids.items() if filename is not None
    ]
    docs_missing = [
        doc_id for doc_id, filename in s3_doc_ids.items() if filename is None
    ]

    LOGGER.info(f"Found {len(docs_found)}/{len(doc_ids)} parser outputs in S3.")

    if docs_missing:
        LOGGER.info(f"Missing: {_n + _n.join(docs_missing)}")

    LOGGER.info("Reading parser outputs from S3...")
    for doc_id, filename in s3_doc_ids.items():
        if filename is None:
            continue

        try:
            doc_id_json_map[doc_id] = json.loads((s3_dir / filename).read_text())
        except json.decoder.JSONDecodeError:
            LOGGER.error(f"Document {doc_id} has invalid JSON.")
            doc_id_json_map[doc_id] = None

    return doc_id_json_map


@click.command()
@click.argument(
    "old_csv_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "new_csv_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "output_dir", type=click.Path(exists=False, file_okay=False, path_type=Path)
)
def run_cli(old_csv_path: Path, new_csv_path: Path, output_dir: Path):
    """Run the CLI."""

    if not output_dir.exists():
        LOGGER.warning(f"Output directory {output_dir} does not exist. Creating...")
        output_dir.mkdir(parents=True)

    load_dotenv(find_dotenv())

    if "EMBEDDINGS_INPUT_S3_PATH" not in os.environ:
        raise ValueError("EMBEDDINGS_INPUT_S3_PATH environment variable not set.")

    s3_dir = S3Path(os.environ["EMBEDDINGS_INPUT_S3_PATH"])
    assert isinstance(s3_dir, S3Path)

    doc_ids = get_new_document_ids_from_csv(old_csv_path, new_csv_path)

    LOGGER.info(f"Found {len(doc_ids)} new documents in the new CSV.")

    doc_id_json_map = get_parser_outputs_from_s3(s3_dir, doc_ids)

    LOGGER.info(f"Found {len(doc_id_json_map)} parser outputs.")
    breakpoint()

    # _continue = Confirm.ask("Continue?")

    LOGGER.info("Writing parser outputs to disk...")
    for doc_id, json_obj in doc_id_json_map.items():
        if json_obj is None:
            continue

        (output_dir / f"{doc_id}.json").write_text(json.dumps(json_obj, indent=4))
    LOGGER.info("Done.")


if __name__ == "__main__":
    run_cli()
