import os
from pathlib import Path
from tempfile import TemporaryDirectory
import logging

import pandas as pd
import wandb
from setfit import SetFitModel
import click
from cpr_data_access.models import Span
from dotenv import load_dotenv, find_dotenv

from utils import load_text_block_sample, predict_from_text_blocks

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)


@click.command()
@click.option(
    "--wandb-artifact-name",
    help="Weights and Biases artifact name. Should start with climatepolicyradar/. E.g. climatepolicyradar/sector-text-classifier/sector-text-classifier:v0",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Output directory for the spans.csv file.",
)
@click.option(
    "--spans-csv-filename",
    type=str,
    default="spans.csv",
    help="The filename to use for the spans CSV output file, including the .csv extension",
)
def cli(wandb_artifact_name: str, output_dir: Path, spans_csv_filename: str) -> None:
    """
    Run a classifier from weights and biases on the full dataset.

    :param str wandb_artifact_name: should start with climatepolicyradar/. E.g. climatepolicyradar/sector-text-classifier/sector-text-classifier:v0
    """

    load_dotenv(find_dotenv(), override=True)

    api = wandb.Api()
    artifact = api.artifact(wandb_artifact_name, type="model")

    with TemporaryDirectory() as temp_dir:
        artifact_dir = artifact.download(temp_dir)
        model = SetFitModel._from_pretrained(artifact_dir)
        class_names = (Path(artifact_dir) / "class_names.txt").read_text().splitlines()

    LOGGER.info("Loading text blocks for all documents...")
    text_blocks_and_metadata = load_text_block_sample(
        docs_dir=Path(os.environ["DOCS_DIR_GST"]).expanduser(),
        num_docs=None,
        text_blocks_per_doc=None,
    )

    LOGGER.info(f"Predicting using classifier {wandb_artifact_name}...")
    predictions_df = predict_from_text_blocks(
        model=model,
        text_blocks_and_doc_metadata=text_blocks_and_metadata,
        class_names=class_names,
    )
    spans = []

    for _, row in predictions_df.iterrows():
        for pred_class in row["predictions"]:
            spans.append(
                Span(
                    document_id=row["document_id"],
                    text_block_text_hash=row["text_hash"],
                    type=pred_class,
                    id=pred_class,
                    text=row["text"],
                    start_idx=0,
                    end_idx=len(row["text"]),
                    sentence=row["text"],
                    pred_probability=1,  # TODO: replace with pred probability
                    annotator=wandb_artifact_name,
                )
            )

    spans_df = pd.DataFrame.from_records([s.dict() for s in spans])

    spans_output_path = output_dir / spans_csv_filename

    if not spans_output_path.parent.exists():
        spans_output_path.parent.mkdir(parents=True)

    spans_output_path.write_text(spans_df.to_csv(index=False))
    LOGGER.info(f"Spans written to {spans_output_path}")


if __name__ == "__main__":
    cli()
