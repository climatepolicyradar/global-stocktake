from pathlib import Path
from typing import Optional
from datetime import datetime

import click
from explorer.main import run_explorer
from classifiers.run_on_full_dataset import run_on_full_dataset
import pandas as pd

from src.cli.utils import get_logger
from src.data.split_spans_csvs import MAX_SPANS_PER_FILE

LOGGER = get_logger(__name__)

EXPLORER_CONCEPTS_NON_ML = [
    "adaptation",
    "barriers-and-challenges",
    "capacity-building",
    "climate-related-hazards",
    "deforestation",
    "equity-and-just-transition",
    "fossil-fuels",
    "good-practice-and-opportunities",
    "greenhouse-gases",
    "international-cooperation",
    "loss-and-damage",
    "mitigation",
    "renewables",
    "response-measures",
    "technologies-br-adaptation-br",
    "technologies-br-mitigation-br",
    "vulnerable-groups",
]

EXPLORER_CONCEPTS_ML = ["financial-flows"]

CLASSIFIER_CONCEPTS = {
    "sectors": "climatepolicyradar/sector-text-classifier/sector-text-classifier:latest",
    "policy-instruments": "climatepolicyradar/policy-instrument-text-classifier/policy-instrument-text-classifier:latest",
}


@click.command()
@click.argument(
    "docs_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--spans-csv-filename", type=str, default=None)
def main(docs_dir: Path, spans_csv_filename: Optional[str] = None):
    """Run concept extraction on new parser outputs."""

    if spans_csv_filename is not None and not spans_csv_filename.endswith(".csv"):
        raise ValueError("spans_csv_filename must end with .csv")

    if spans_csv_filename is None:
        timestr = datetime.now().strftime("%Y%m%d-%H%M%S")
        LOGGER.info(
            f"No spans CSV filename provided. Using default of spans_{timestr}.csv."
        )
        spans_csv_filename = f"spans_{timestr}.csv"

    LOGGER.info("Running non-ML concepts...")
    for concept in EXPLORER_CONCEPTS_NON_ML:
        run_explorer(
            dataset_name="gst",
            input_path=f"./concepts/{concept}/input.xlsx",
            output_dir=f"./concepts/{concept}",
            data_dir=str(docs_dir),
            spans_csv_filename=spans_csv_filename,
        )

    for concept in EXPLORER_CONCEPTS_ML:
        run_explorer(
            dataset_name="gst",
            input_path=f"./concepts/{concept}/input.xlsx",
            output_dir=f"./concepts/{concept}",
            data_dir=str(docs_dir),
            spans_csv_filename=spans_csv_filename,
            use_transformer=True,
        )

    for concept, wandb_artifact_name in CLASSIFIER_CONCEPTS.items():
        run_on_full_dataset(
            wandb_artifact_name=wandb_artifact_name,
            output_dir=Path(f"./concepts/{concept}"),
            spans_csv_filename=spans_csv_filename,
            extra_output=True,
        )

    LOGGER.info("Splitting large spans CSV files...")
    for concept in (
        EXPLORER_CONCEPTS_ML
        + EXPLORER_CONCEPTS_NON_ML
        + list(CLASSIFIER_CONCEPTS.keys())
    ):
        spans_csv_path = Path(f"./concepts/{concept}/{spans_csv_filename}")
        if not spans_csv_path.exists():
            LOGGER.info(f"No {spans_csv_path} file found. Skipping.")
            continue

        spans_df = pd.read_csv(spans_csv_path)
        if len(spans_df) > MAX_SPANS_PER_FILE:
            LOGGER.info(f"Splitting {concept} spans CSV file into multiple files.")
            split_dfs = [
                spans_df[i : i + MAX_SPANS_PER_FILE]
                for i in range(0, len(spans_df), MAX_SPANS_PER_FILE)
            ]

            for idx, df in enumerate(split_dfs):
                df.to_csv(
                    spans_csv_path.parent / f"{spans_csv_path.stem}_{idx}.csv",
                    index=False,
                )

            spans_csv_path.unlink()


if __name__ == "__main__":
    main()
