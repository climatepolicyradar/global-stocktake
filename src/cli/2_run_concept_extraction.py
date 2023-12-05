from pathlib import Path
from typing import Optional
from datetime import datetime

import click
from explorer.main import run_explorer
from classifiers.run_on_full_dataset import run_on_full_dataset

from src.cli.utils import get_logger

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

    # TODO: classifier concepts
    for concept, wandb_artifact_name in CLASSIFIER_CONCEPTS.items():
        run_on_full_dataset(
            wandb_artifact_name=wandb_artifact_name,
            output_dir=Path(f"./concepts/{concept}"),
            spans_csv_filename=spans_csv_filename,
            extra_output=True,
        )


if __name__ == "__main__":
    main()
