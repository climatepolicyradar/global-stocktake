"""Split large spans.csv files in the concepts directory into separate files, to make them commitable to git. First argument is optional filename to split, which defaults to "spans.csv" if not specified."""

from pathlib import Path
import logging
import sys

import pandas as pd

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

MAX_SPANS_PER_FILE = 50_000

if __name__ == "__main__":
    spans_filename = sys.argv[1] if len(sys.argv) > 1 else "spans.csv"

    for concept_dir in (Path(__file__).parent.parent.parent / "concepts").iterdir():
        if not concept_dir.is_dir():
            continue

        if not (concept_dir / spans_filename).exists():
            LOGGER.info(
                f"No {spans_filename} file found in {concept_dir.name} directory. Skipping"
            )
            continue

        spans_df = pd.read_csv(concept_dir / spans_filename)
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

        LOGGER.info(
            f"Splitting {concept_dir/spans_filename} into {len(split_dfs)} files"
        )

        for idx, df in enumerate(split_dfs):
            df.to_csv(
                concept_dir / f"{Path(spans_filename).stem}_{idx}.csv", index=False
            )

        # Delete the original spans.csv file.
        (concept_dir / spans_filename).unlink()
