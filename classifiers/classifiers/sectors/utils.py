from typing import Dict, Optional

import evaluate
import numpy as np
from setfit import SetFitModel


def compute_metrics(y_pred: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Compute metrics for the model predictions.

    Args:
        y_pred: The predictions from the model.
        y_test: The actual labels.

    Returns:
        A dictionary of metrics including F1, Precision, Recall, and Accuracy.
    """
    multilabel_f1_metric = evaluate.load("f1", "multilabel")
    multilabel_precision_metric = evaluate.load("precision", "multilabel")
    multilabel_recall_metric = evaluate.load("recall", "multilabel")
    multilabel_accuracy_metric = evaluate.load("accuracy", "multilabel")

    return {
        "f1": multilabel_f1_metric.compute(
            predictions=y_pred, references=y_test, average="micro"
        )["f1"],
        "precision": multilabel_precision_metric.compute(
            predictions=y_pred, references=y_test, average="micro"
        )["precision"],
        "recall": multilabel_recall_metric.compute(
            predictions=y_pred, references=y_test, average="micro"
        )["recall"],
        "accuracy": multilabel_accuracy_metric.compute(
            predictions=y_pred, references=y_test
        )["accuracy"],
    }


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
