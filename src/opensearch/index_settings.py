SEARCHABLE_FIELDS = {"text"}
KEYWORD_FIELDS = {
    "id",
    "type",
    "document_id",
    "span_ids",
    "span_types",
    "document_metadata.link",
    "document_metadata.party",
    "document_metadata.theme",
    "document_metadata.topics",
    "document_metadata.translation",
    "document_metadata.data_error_type",
}

index_settings = {
    "settings": {
        "analysis": {
            "filter": {
                "ascii_folding_preserve_original": {
                    "type": "asciifolding",
                    "preserve_original": True,
                }
            },
            # This analyser folds non-ASCII characters into ASCII equivalents, but preserves the original.
            # E.g. a search for "é" will return results for "e" and "é".
            "analyzer": {
                "folding": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ascii_folding_preserve_original"],
                }
            },
            # This normalizer does the same as the folding analyser, but is used for keyword fields.
            "normalizer": {
                "folding": {
                    "type": "custom",
                    "char_filter": [],
                    "filter": ["lowercase", "asciifolding"],
                }
            },
        },
    },
    "mappings": {
        "properties": {
            field: {"type": "text", "analyzer": "folding"}
            for field in SEARCHABLE_FIELDS
        }
        | {
            field: {"type": "keyword", "normalizer": "folding"}
            for field in KEYWORD_FIELDS
        },
    },
}
