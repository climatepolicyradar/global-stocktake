import os

import click
import argilla as rg
import evaluate
import numpy as np
import wandb
from datasets import Dataset
from dotenv import load_dotenv, find_dotenv
from setfit import SetFitModel
from setfit import SetFitTrainer
from sklearn.preprocessing import MultiLabelBinarizer
from skmultilearn.model_selection import iterative_train_test_split


def model_init(params):
    params = params or {}
    max_iter = params.get("max_iter", 10)
    solver = params.get("solver", "liblinear")
    params = {
        "head_params": {
            "max_iter": max_iter,
            "solver": solver,
        },
        "multi_target_strategy": "multi-output"
    }
    return SetFitModel.from_pretrained("sentence-transformers/paraphrase-mpnet-base-v2", **params)

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



@click.command()
@click.option('--dataset-name', default='sectors-sentence-or-text-block', help='Dataset name')
@click.option('--num-iterations', default=[5, 10, 20], type=click.IntRange(1, 100, clamp=True), multiple=True, help='Number of iterations')
def cli(dataset_name, num_iterations):
    wandb.init(project="my_project", config={
        "dataset_name": dataset_name,
        "num_iterations": num_iterations,
    })
    load_dotenv(find_dotenv(), override=True)


    # User management is done at a workspace level
    rg.init(
        workspace="gst",
        api_key=os.environ["ARGILLA_API_KEY"],
    )

    dataset = rg.load(dataset_name).to_datasets()
    dataset_df = dataset.to_pandas()

    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(dataset_df["annotation"].values)
    X = dataset_df["text"].values.reshape(-1)
    X = np.reshape(X, (X.size, 1))

    X_train, y_train, X_test, y_test = iterative_train_test_split(X, y, test_size=0.3)
    X_train_1d = np.array([i[0] for i in X_train])
    X_test_1d = np.array([i[0] for i in X_test])

    train_dataset = Dataset.from_dict({"text": X_train_1d, "label": y_train})
    test_dataset = Dataset.from_dict({"text": X_test_1d, "label": y_test})



    trainer_hp = SetFitTrainer(
        model_init=model_init,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        metric=compute_metrics,
    )

    def hp_space(trial):  # Training parameters
        return {
            "num_iterations": trial.suggest_categorical("num_iterations", num_iterations),
        }

    best_run = trainer_hp.hyperparameter_search(direction="maximize", hp_space=hp_space, n_trials=3)
    wandb.log(best_run)

if __name__ == '__main__':
    cli()
