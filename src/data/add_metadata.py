"""Converting documents from BaseDocument to GSTDocument as defined by the data access libary."""

import pandas as pd
from cpr_data_access.models import BaseDocument, GSTDocument, GSTDocumentMetadata


def base_document_to_gst_document(
    document: BaseDocument, scraper_data: pd.DataFrame
) -> GSTDocument:
    """
    Convert a BaseDocument to a GSTDocument by adding metadata to it from the scraper CSV.

    :param BaseDocument document: document without metadata
    :param pd.DataFrame scraper_data: loaded using `src.data.load_scraper_csv`
    :raises Exception: if no document exists in the scraper data with md5sum equal to the document's
    :return GSTDocument: document with added metadata
    """
    if document.document_md5_sum not in scraper_data["md5sum"].tolist():
        raise Exception(
            f"No document exists in the scraper data with md5sum equal to the document's: {document.document_md5_sum}"
        )

    doc_dict = document.dict(exclude={"document_metadata"})
    new_metadata_dict = scraper_data.loc[
        scraper_data["md5sum"] == document.document_md5_sum
    ].to_dict(orient="records")[0]
    new_metadata = GSTDocumentMetadata.parse_obj(new_metadata_dict)

    return GSTDocument(**doc_dict, document_metadata=new_metadata)
