import os
import logging
import argilla as rg
import click
import numpy as np
from typing import Optional, Dict
from datasets import Dataset
from dotenv import load_dotenv, find_dotenv
from setfit import SetFitModel, SetFitTrainer
from sklearn.preprocessing import MultiLabelBinarizer
from skmultilearn.model_selection import iterative_train_test_split

import wandb
from utils import compute_metrics, model_init

logging.basicConfig(level=logging.INFO)



@click.command()
@click.option(
    "--dataset-name", help="Dataset name"
)
@click.option(
    "--num-iterations",
    default=[5, 10, 20],
    type=click.IntRange(1, 100, clamp=True),
    multiple=True,
    help="Number of iterations",
)
@click.option(
    "--test-size", default=0.3, help="Fraction of the dataset to be used as test split."
)
def cli(dataset_name: str, num_iterations: list[int], test_size: float):
    """
    Main CLI function for the script.

    Args:
        dataset_name: Name of the dataset to be loaded.
        num_iterations: List of possible iteration numbers for the model.
        test_size: Fraction of the dataset to be used as test split.
    """
    wandb.init(
        project="sectors-classifier-gst",
        config={
            "dataset_name": dataset_name,
            "num_iterations": num_iterations,
            "job_type": "hyperparameter_searcg"
        },
    )
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

    X_train, y_train, X_test, y_test = iterative_train_test_split(
        X, y, test_size=test_size
    )
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
            "num_iterations": trial.suggest_categorical(
                "num_iterations", num_iterations
            ),
        }

    best_run = trainer_hp.hyperparameter_search(
        direction="maximize", hp_space=hp_space, n_trials=3
    )
    wandb.log(best_run)


if __name__ == "__main__":
    cli()
