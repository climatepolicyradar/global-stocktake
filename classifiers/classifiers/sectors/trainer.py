import os
import logging
from collections import defaultdict

import argilla as rg
import click
import numpy as np
import torch
from datasets import Dataset
from dotenv import load_dotenv, find_dotenv
from setfit import SetFitModel, SetFitTrainer
from sklearn.preprocessing import MultiLabelBinarizer
from skmultilearn.model_selection import IterativeStratification

import wandb
from utils import compute_metrics

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def model_init(params: dict = None) -> SetFitModel:
    """
    Initialize the SetFitModel.

    params (dict): a dictionary containing parameters for the model.
    Default is None.

    Returns:
    SetFitModel: a SetFitModel object with specified parameters.
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


@click.command()
@click.option("--argilla-dataset-name", help="Dataset name")
@click.option("--num-iterations", default=10, help="Number of iterations")
@click.option("--n-folds", default=5, help="Number of folds")
@click.option("--batch-size", default=12, help="Batch size")
def cli(
    argilla_dataset_name: str,
    num_iterations: int = 5,
    n_folds: int = 5,
    batch_size: int = 12,
) -> None:
    """Command Line Interface function for the script."""
    logger.info("Initiating Weights & Biases...")
    wandb.init(
        project="sectors-classifier-gst",
        config={
            "dataset_name": argilla_dataset_name,
            "num_iterations": num_iterations,
            "n_folds": n_folds,
        },
    )

    logger.info("Loading environment variables...")
    load_dotenv(find_dotenv(), override=True)

    # User management is done at a workspace level
    logger.info("Initializing Argilla...")
    rg.init(
        workspace="gst",
        api_key=os.environ["ARGILLA_API_KEY"],
    )

    logger.info("Loading dataset...")
    dataset = rg.load(argilla_dataset_name).to_datasets()
    dataset_df = dataset.to_pandas()
    dataset_df = dataset_df.dropna(subset=["annotation"])

    logger.info("Preprocessing data...")
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(dataset_df["annotation"].values)
    X = dataset_df["text"].values.reshape(-1)
    X = np.reshape(X, (X.size, 1))

    all_metrics = defaultdict(list)
    k_fold = IterativeStratification(n_splits=n_folds, order=1)

    logger.info("Starting model training and evaluation...")
    for ix, (train, test) in enumerate(k_fold.split(X, y)):
        model = model_init()  # Use our model_init function here
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
        logger.info(f"Starting training for fold {ix + 1}...")
        trainer.train()
        logger.info("Evaluating model...")
        metrics = trainer.evaluate()
        all_metrics[ix] = metrics
        wandb.log(metrics)

        # clean up
        logger.info("Cleaning up...")
        del model
        del trainer
        torch.cuda.empty_cache()  # Clear CUDA cache after each fold

    logger.info("Script execution completed.")


if __name__ == "__main__":
    cli()
