"""CLI to generate JSON inputs for the PDF parser based on the scraper output."""

from pathlib import Path
from typing import Optional, Generator

import requests as requests
from cloudpathlib import S3Path
from pydantic import BaseModel, AnyHttpUrl
import pandas as pd
from tqdm.auto import tqdm
import click


class ParserInput(BaseModel):
    """Base class for input to a parser."""

    document_id: str
    document_metadata: dict
    document_name: str
    document_description: str
    document_source_url: Optional[AnyHttpUrl]
    document_cdn_object: Optional[str]
    document_content_type: Optional[str]
    document_md5_sum: Optional[str]
    document_slug: str


def scraper_csv_to_parser_inputs(
    input_path: Path,
) -> Generator[ParserInput, None, None]:
    """Iterate through the GST scraper output CSV and yield ParserInput objects to be consumed by the PDF parser."""

    scraper_output = pd.read_csv(input_path)
    scraper_output["pdf_filename"] = scraper_output["pdf_link"].apply(
        lambda i: i.split("/")[-1]
    )

    for idx, row in tqdm(scraper_output.iterrows(), total=len(scraper_output)):
        yield ParserInput(
            document_id=f"GST.{idx}",
            document_metadata={},
            document_name=Path(row["pdf_filename"]).stem,
            document_description="Document relating to the global stock take.",
            document_source_url=row["pdf_link"],
            document_cdn_object=f"{row['pdf_filename']}",
            document_content_type="application/pdf",
            document_md5_sum=row["md5sum"],
            document_slug=f"{Path(row['pdf_filename']).stem}_slug",
        )


@click.command()
@click.argument("scraper_csv_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--pdfs-dir", type=str)
@click.option("--output-path", type=str)
def main(scraper_csv_path: Path, pdfs_dir: str, output_path: str):
    if pdfs_dir.startswith("s3://"):
        pdfs_dir_as_path = S3Path(pdfs_dir)
    else:
        pdfs_dir_as_path = Path(pdfs_dir)

    if output_path.startswith("s3://"):
        output_path_as_path = S3Path(output_path)
    else:
        output_path_as_path = Path(output_path)

    for parser_input in scraper_csv_to_parser_inputs(scraper_csv_path):
        if not (output_path_as_path / f"{parser_input.document_id}.json").exists():
            (output_path_as_path / f"{parser_input.document_id}.json").write_text(
                parser_input.json(indent=4, ensure_ascii=False)
            )

            # Check that the PDF can be retrieved from the CDN
            if isinstance(pdfs_dir_as_path, S3Path):
                _ = requests.get(
                    f"{pdfs_dir_as_path}/{parser_input.document_cdn_object}"
                )


if __name__ == "__main__":
    main()
