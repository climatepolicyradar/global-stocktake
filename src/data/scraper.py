from pathlib import Path

import pandas as pd
import numpy as np


def load_scraper_csv(scraper_csv_path: Path) -> pd.DataFrame:
    """Load the scraper CSV into a pandas DataFrame."""
    scraper_data = pd.read_csv(scraper_csv_path)

    # Convert columns for pydantic validation
    scraper_data[["Date", "Document Variant"]] = (
        scraper_data[["Date", "Document Variant"]]
        .fillna(np.nan)
        .replace([np.nan], [None])
    )

    # Add a column for the filename of the PDF, used to generate input JSONs for the parser
    scraper_data["pdf_name"] = (
        scraper_data["Documents"]
        .apply(lambda i: i.split("/")[-1][:-4])
        .apply(lambda i: i.replace("%", ""))
    )

    return scraper_data
