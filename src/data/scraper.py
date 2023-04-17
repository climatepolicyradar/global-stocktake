from pathlib import Path

import pandas as pd
import numpy as np


def load_scraper_csv(scraper_csv_path: Path) -> pd.DataFrame:
    """Load the scraper CSV into a pandas DataFrame."""
    scraper_data = pd.read_csv(scraper_csv_path)

    # Convert columns for pydantic validation
    scraper_data[["data_error_type", "date", "topics", "party"]] = (
        scraper_data[["data_error_type", "date", "topics", "party"]]
        .fillna(np.nan)
        .replace([np.nan], [None])
    )
    scraper_data["topics"] = scraper_data["topics"].apply(
        lambda i: i.split(",") if i is not None else i
    )

    # Add a column for the filename of the PDF, used to generate input JSONs for the parser
    scraper_data["pdf_name"] = (
        scraper_data["pdf_link"]
        .apply(lambda i: i.split("/")[-1][:-4])
        .apply(lambda i: i.replace("%", ""))
    )

    return scraper_data
