import evaluate

def compute_metrics(y_pred, y_test):
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