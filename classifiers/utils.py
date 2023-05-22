from typing import Dict, Optional, Sequence
from pathlib import Path
import random

import evaluate
import numpy as np
from setfit import SetFitModel
import pandas as pd
from cpr_data_access.models import TextBlock, BaseDocument
from cpr_data_access.models import Dataset as CPRDataset
from tqdm.auto import tqdm


def compute_metrics(
    y_pred: np.ndarray, y_test: np.ndarray, class_names: list[str]
) -> Dict[str, float]:
    """
    Compute sample level and class level metrics for multilabel predictions.

    Args:
        y_pred: The predictions from the model.
        y_test: The actual labels.
        class_names: The names of the classes.

    Returns:
        A dictionary of metrics including F1, Precision, Recall, and Accuracy.
    """
    multilabel_f1_metric = evaluate.load("f1", "multilabel")
    multilabel_precision_metric = evaluate.load("precision", "multilabel")
    multilabel_recall_metric = evaluate.load("recall", "multilabel")
    multilabel_accuracy_metric = evaluate.load("accuracy", "multilabel")

    sample_metrics = {
        "f1": multilabel_f1_metric.compute(
            predictions=y_pred, references=y_test, average="samples"
        )["f1"],
        "precision": multilabel_precision_metric.compute(
            predictions=y_pred, references=y_test, average="samples"
        )["precision"],
        "recall": multilabel_recall_metric.compute(
            predictions=y_pred, references=y_test, average="samples"
        )["recall"],
        "accuracy": multilabel_accuracy_metric.compute(
            predictions=y_pred, references=y_test
        )["accuracy"],
    }

    per_class_metrics = (
        multilabel_f1_metric.compute(
            predictions=y_pred, references=y_test, average=None
        )
        | multilabel_precision_metric.compute(
            predictions=y_pred, references=y_test, average=None
        )
        | multilabel_recall_metric.compute(
            predictions=y_pred, references=y_test, average=None
        )
    )

    per_class_metrics_by_class = dict()

    for idx, class_name in enumerate(class_names):
        f1_score = per_class_metrics["f1"][idx]
        precision_score = per_class_metrics["precision"][idx]
        recall_score = per_class_metrics["recall"][idx]

        per_class_metrics_by_class[class_name] = {
            "f1": f1_score,
            "precision": precision_score,
            "recall": recall_score,
        }

    return {"sample_avg": sample_metrics, "per_class": per_class_metrics_by_class}


def model_init(params: Optional[Dict] = None) -> SetFitModel:
    """
    Initialize the model with given parameters or default parameters.

    Args:
        params: A dictionary of parameters.

    Returns:
        A SetFitModel instance.
    """
    params = params or {}
    max_iter = params.get("max_iter", 10)
    solver = params.get("solver", "liblinear")
    params = {
        "head_params": {
            "max_iter": max_iter,
            "solver": solver,
        },
        "multi_target_strategy": "multi-output",
    }
    return SetFitModel.from_pretrained(
        "sentence-transformers/paraphrase-mpnet-base-v2", **params
    )


def load_text_block_sample(
    docs_dir: Path,
    num_docs: Optional[int] = None,
    text_blocks_per_doc: Optional[int] = None,
    random_state: int = 42,
) -> Sequence[tuple[TextBlock, dict]]:
    """
    Load a sample of English language text blocks and associated document metadata from the database.

    Excludes GST-specific metadata (documents are loaded as BaseDocument objects).

    :param num_docs: number of docs to sample from the dataset. If None, sample all docs.
    :param text_blocks_per_doc: max number of text blocks to sample per document. If None, sample all text blocks.
    :param random_state: random state, for reproducibility
    :return Sequence[tuple[TextBlock, dict]]: tuples of text block objects and dictionaries providing any context
    """

    random.seed(random_state)

    dataset = (
        CPRDataset(BaseDocument)
        .load_from_local(str(docs_dir), limit=num_docs)
        .filter_by_language("en")
    )

    text_blocks_doc_metadata_sample = []

    for document in tqdm(dataset.documents):
        if document.text_blocks is None:
            print(f"Skipping {document.document_id} as no text blocks")
            continue

        doc_metadata = document.dict(exclude={"text_blocks", "page_metadata"})

        # Randomly sample a fixed number of text blocks per document
        if (text_blocks_per_doc is None) or (
            len(document.text_blocks) <= text_blocks_per_doc
        ):
            blocks = document.text_blocks
        else:
            blocks = random.sample(document.text_blocks, text_blocks_per_doc)

        text_blocks_doc_metadata_sample += zip(blocks, [doc_metadata] * len(blocks))

    return text_blocks_doc_metadata_sample


def predict_from_text_blocks(
    model: SetFitModel,
    text_blocks_and_doc_metadata: Sequence[tuple[TextBlock, dict]],
    class_names: list[str],
) -> pd.DataFrame:
    """
    Given a setfit model and a list of text blocks and dictionaries providing any context, return a dataframe with the predictions and associated metadata.

    :param model: setfit model
    :param Sequence[tuple[TextBlock, dict]] text_blocks_and_doc_metadata: tuples of text block objects and dictionaries providing any context
    :param list[str] class_names: class names in order e.g. from the multilabel binarizer
    :return pd.DataFrame: dataframe with one-hot encoded predictions and associated metadata
    """

    text = [
        block.to_string().replace("\n", " ").replace("  ", " ")
        for (block, _) in text_blocks_and_doc_metadata
    ]
    y_pred = model.predict(text, as_numpy=False)
    y_pred_df = pd.DataFrame(y_pred, columns=class_names)  # type: ignore

    metadata = [
        {"text": text[idx], "text_hash": block.text_hash}
        | block.dict(include={"language", "text_block_id", "type", "page_number"})
        | metadata_dict
        for idx, (block, metadata_dict) in enumerate(text_blocks_and_doc_metadata)
    ]
    metadata_df = pd.DataFrame.from_records(metadata)

    predictions_df = pd.concat([metadata_df, y_pred_df], axis=1)

    # Add a column with list of predicted classes
    predictions_df["predictions"] = predictions_df.apply(
        lambda row: row[class_names].index[row[class_names] == 1].tolist(), axis=1
    )

    return predictions_df
