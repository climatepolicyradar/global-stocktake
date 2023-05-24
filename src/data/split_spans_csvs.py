"""Split large spans.csv files in the concepts directory into separate files, to make them commitable to git."""

from pathlib import Path
import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

MAX_SPANS_PER_FILE = 50000

if __name__ == "__main__":
    for concept_dir in (Path(__file__).parent.parent.parent / "concepts").iterdir():
        if not concept_dir.is_dir():
            continue

        if not (concept_dir / "spans.csv").exists():
            LOGGER.info(
                f"No concepts.csv file found in {concept_dir.name} directory. Skipping"
            )
            continue

        spans_df = pd.read_csv(concept_dir / "spans.csv")
        if len(spans_df) < MAX_SPANS_PER_FILE:
            LOGGER.info(
                f"Concept {concept_dir.name} has fewer than {MAX_SPANS_PER_FILE} spans. Skipping"
            )
            continue

        # Split dataframe into multiple dataframes, each with a maximum of MAX_SPANS_PER_FILE rows.
        split_dfs = [
            spans_df[i : i + MAX_SPANS_PER_FILE]
            for i in range(0, len(spans_df), MAX_SPANS_PER_FILE)
        ]

        LOGGER.info(f"Splitting {concept_dir/'spans.csv'} into {len(split_dfs)} files")

        for idx, df in enumerate(split_dfs):
            df.to_csv(concept_dir / f"spans_{idx}.csv", index=False)

        # Delete the original spans.csv file.
        (concept_dir / "spans.csv").unlink()
