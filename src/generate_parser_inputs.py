"""CLI to generate JSON inputs for the PDF parser based on the scraper output."""

from pathlib import Path
from typing import Optional
from typing import Union

import requests as requests
from cloudpathlib import S3Path
from pydantic import BaseModel, AnyHttpUrl


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


class PdfFileGenerator:
    def __init__(self, input_dir: Union[Path, S3Path], output_dir: Union[Path, S3Path]):
        """
        Yields objects of the ParserInput type for pdf documents in a s3/directory.
        :param input_dir: directory of input PDF files
        :param output_dir: directory of output JSON files (results)
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.files = self.input_dir.glob("*.pdf")

    def get_pdfs(self) -> tuple[ParserInput, Union[Path, S3Path]]:
        """Yield the ParserInput objects for each pdf in the input directory as well as the path to save the json
        object to."""
        counter = 0
        for file in self.files:
            counter += 1
            yield ParserInput(
                document_id=f"CCLW.gst.{counter}.{counter}",
                document_metadata={},
                document_name=file.stem,
                document_description="Document relating to the global stock take.",
                document_source_url=None,
                document_cdn_object=str(file.key),
                document_content_type="application/pdf",
                document_md5_sum=None,
                document_slug=f"{file.stem}_slug",
            ), self.output_dir / f"CCLW.gst.{counter}.{counter}.json"


if __name__ == "__main__":
    CDN_DOMAIN = ""
    input_path = S3Path("")
    output_path = S3Path("")
    for parser_input, write_path in PdfFileGenerator(
        input_path, output_path
    ).get_pdfs():
        if not write_path.exists():
            write_path.write_text(parser_input.json(indent=4, ensure_ascii=False))
            resp = requests.get(
                f"https://{CDN_DOMAIN}/{parser_input.document_cdn_object}"
            )
