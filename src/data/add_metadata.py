"""Converting documents from BaseDocument to GSTDocument as defined by the data access libary."""

import pandas as pd
from cpr_data_access.models import BaseDocument, GSTDocument, GSTDocumentMetadata


def base_document_to_gst_document(
    document: BaseDocument, scraper_data: pd.DataFrame
) -> GSTDocument:
    """
    Convert a BaseDocument to a GSTDocument by adding metadata to it from the scraper CSV.

    Documents are matched by source URL, as md5sum is not availabe in the scraper CSV.

    :param BaseDocument document: document without metadata
    :param pd.DataFrame scraper_data: loaded using `src.data.load_scraper_csv`
    :raises Exception: if no document exists in the scraper data with md5sum equal to the document's
    :return GSTDocument: document with added metadata
    """
    if document.document_id not in scraper_data["CPR Document ID"].tolist():
        raise Exception(
            f"No document exists in the scraper data with ID equal to the document's: {document.document_id}"
        )

    doc_dict = document.dict(exclude={"document_metadata", "_text_block_idx_hash_map"})
    new_metadata_dict = scraper_data.loc[
        scraper_data["CPR Document ID"] == document.document_id
    ].to_dict(orient="records")[0]

    new_metadata_dict["source"] = "GST-related documents"
    new_metadata_dict["types"] = [
        s.strip() for s in new_metadata_dict.pop("Submission Type").split(",")
    ]
    new_metadata_dict["author"] = [
        s.strip() for s in new_metadata_dict.pop("Author").split(",")
    ]
    new_metadata_dict["validation_status"] = "validated"
    new_metadata_dict["version"] = new_metadata_dict.pop("Document Role")
    new_metadata_dict["date"] = new_metadata_dict.pop("Date")
    new_metadata_dict["link"] = new_metadata_dict.get("Documents")
    new_metadata_dict["document_variant"] = new_metadata_dict.pop("Document Variant")
    new_metadata_dict["author_is_party"] = new_metadata_dict["Author Type"] == "Party"
    new_metadata_dict["family_id"] = new_metadata_dict.pop("CPR Family ID")
    new_metadata_dict["family_slug"] = new_metadata_dict.pop("CPR Family Slug")
    new_metadata_dict["family_name"] = new_metadata_dict.pop("Family Name")
    new_metadata_dict["geography_iso"] = new_metadata_dict.pop("Geography ISO")
    # NOTE: the document URL is also stored in the JSON, but is populated with "https://example.com" when the standalone parser is used to process just a PDF
    new_metadata_dict["document_source_url"] = new_metadata_dict.pop("Documents")
    new_metadata_dict["status"] = ""

    new_metadata = GSTDocumentMetadata.parse_obj(new_metadata_dict)

    # TODO: changing the document title manually should only need to be done because we're using old parser outputs.
    # Eventually the clean title should come from the new parser outputs.
    doc_dict["document_name"] = new_metadata_dict["Document Title"]

    return GSTDocument(**doc_dict, document_metadata=new_metadata)
