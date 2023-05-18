import os
from collections import defaultdict

import argilla as rg
import click
import numpy as np
import torch
from datasets import Dataset
from dotenv import load_dotenv, find_dotenv
from setfit import SetFitModel
from setfit import SetFitTrainer
from sklearn.preprocessing import MultiLabelBinarizer
from skmultilearn.model_selection import IterativeStratification
from skmultilearn.model_selection import iterative_train_test_split

import wandb
from utils import compute_metrics


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

@click.command()
@click.option('--argilla-dataset-name', help='Dataset name')
@click.option('--num-iterations', default=20, help='Number of iterations')
@click.option('--n-folds', default=5, help='Number of folds')
@click.option('--batch-size', default=8, help='Batch size')
def cli(argilla_dataset_name, num_iterations: int =20, n_folds: int = 5, batch_size: int = 8):
    wandb.init(project="sectors-classifier-gst", config={
        "dataset_name": argilla_dataset_name,
        "num_iterations": num_iterations,
        "n_folds": n_folds
    })

    load_dotenv(find_dotenv(), override=True)

    # User management is done at a workspace level
    rg.init(
        workspace="gst",
        api_key=os.environ["ARGILLA_API_KEY"],
    )

    dataset = rg.load(argilla_dataset_name).to_datasets()
    dataset_df = dataset.to_pandas()
    dataset_df = dataset_df.dropna(subset=["annotation"])

    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(dataset_df["annotation"].values)
    X = dataset_df["text"].values.reshape(-1)
    X = np.reshape(X, (X.size, 1))

    # X_train, y_train, X_test, y_test = iterative_train_test_split(X, y, test_size=0.3)

    all_metrics = defaultdict(list)
    if n_folds > 2:
        # split dataset into k-folds using iterative stratification and loop over folds
        # to get metrics.
        k_fold = IterativeStratification(n_splits=n_folds, order=1)

        for ix, (train, test) in enumerate(k_fold.split(X, y)):
            model = SetFitModel.from_pretrained(
                "sentence-transformers/paraphrase-mpnet-base-v2",
                multi_target_strategy="multi-output",  # one-vs-rest; multi-output; classifier-chain
            )
            X_train_1d = X[train].reshape(-1)
            X_test_1d = X[test].reshape(-1)
            y_train = y[train]
            y_test = y[test]
            train_dataset = Dataset.from_dict({"text": X_train_1d, "label": y_train})
            test_dataset = Dataset.from_dict({"text": X_test_1d, "label": y_test})
            trainer = SetFitTrainer(
                model=model,
                train_dataset=train_dataset,
                eval_dataset=test_dataset,
                metric=compute_metrics,
                num_epochs=5,
                num_iterations=num_iterations,
                batch_size=batch_size,
            )
            trainer.train()
            # Save the trained model and get precision, recall, f1 scores
            metrics = trainer.evaluate()
            all_metrics[ix] = metrics
            wandb.log(metrics)

            # clean up
            del model
            del trainer
            torch.cuda.empty_cache() # Clear CUDA cache after each fold
    else:
        # No cross-validation
        model = SetFitModel.from_pretrained(
            "sentence-transformers/paraphrase-mpnet-base-v2",
            multi_target_strategy="multi-output",  # one-vs-rest; multi-output; classifier-chain
        )
        X_train, y_train, X_test, y_test = iterative_train_test_split(X, y, test_size=0.3)

        X_train_1d = X_train.reshape(-1)
        X_test_1d = X_test.reshape(-1)
        train_dataset = Dataset.from_dict({"text": X_train_1d, "label": y})
        test_dataset = Dataset.from_dict({"text": X_test_1d, "label": y})
        trainer = SetFitTrainer(
            model=model,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
            metric=compute_metrics,
            num_epochs=5,
            num_iterations=num_iterations,
            batch_size=batch_size,
        )
        trainer.train()
        # Save the trained model and get precision, recall, f1 scores
        metrics = trainer.evaluate()
        wandb.log(metrics)

        # clean up
        del model
        del trainer
        torch.cuda.empty_cache()  # Clear CUDA cache after each fold





if __name__ == '__main__':
    cli()
