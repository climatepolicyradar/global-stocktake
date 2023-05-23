import os
import logging
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

import argilla as rg
import click
import numpy as np
import torch
from datasets import Dataset
from dotenv import load_dotenv, find_dotenv
from setfit import SetFitTrainer
from sklearn.preprocessing import MultiLabelBinarizer
from skmultilearn.model_selection import IterativeStratification

import wandb
from utils import (
    compute_metrics,
    model_init,
    load_text_block_sample,
    predict_from_text_blocks,
)

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)


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
    LOGGER.info("Initiating Weights & Biases...")
    wandb.init(
        project=argilla_dataset_name,
        config={
            "dataset_name": argilla_dataset_name,
            "num_iterations": num_iterations,
            "n_folds": n_folds,
        },
    )

    LOGGER.info("Loading environment variables...")
    load_dotenv(find_dotenv(), override=True)

    # User management is done at a workspace level
    LOGGER.info("Initializing Argilla...")
    rg.init(
        workspace="gst",
        api_key=os.environ["ARGILLA_API_KEY"],
    )

    LOGGER.info("Loading dataset...")
    dataset = rg.load(argilla_dataset_name).to_datasets()
    dataset_df = dataset.to_pandas()
    dataset_df = dataset_df.dropna(subset=["annotation"])

    wandb.log({"argilla-dataset": dataset})

    LOGGER.info("Preprocessing data...")
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(dataset_df["annotation"].values)
    X = dataset_df["text"].values.reshape(-1)
    X = np.reshape(X, (X.size, 1))

    all_metrics = defaultdict(list)
    k_fold = IterativeStratification(n_splits=n_folds, order=1)

    LOGGER.info(f"Starting model evaluation using {n_folds}-fold cross-validation...")
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
            metric=lambda y_pred, y_test: compute_metrics(y_pred, y_test, mlb.classes_),
            num_epochs=5,
            num_iterations=num_iterations,
            batch_size=batch_size,
        )
        LOGGER.info(f"Starting training for fold {ix + 1}...")
        trainer.train()
        LOGGER.info("Evaluating model...")
        metrics = trainer.evaluate()
        all_metrics[ix] = metrics
        wandb.log(metrics)

        # clean up
        LOGGER.info("Cleaning up...")
        del model
        del trainer
        torch.cuda.empty_cache()  # Clear CUDA cache after each fold

    LOGGER.info("Training classifier on all data")
    model = model_init()
    X_1d = X.reshape(-1)
    train_dataset = Dataset.from_dict({"text": X_1d, "label": y})
    trainer = SetFitTrainer(
        model=model,
        train_dataset=train_dataset,
        num_epochs=5,
        num_iterations=num_iterations,
        batch_size=batch_size,
    )

    LOGGER.info("Starting training...")
    trainer.train()

    LOGGER.info("Loading sample of text blocks and predicting labels...")
    text_blocks_and_metadata = load_text_block_sample(
        docs_dir=Path(os.environ["DOCS_DIR_GST"]),
        num_docs=500,
        text_blocks_per_doc=1,
        random_state=42,
    )
    predictions_df = predict_from_text_blocks(
        model=model,
        text_blocks_and_doc_metadata=text_blocks_and_metadata,
        class_names=list(mlb.classes_),
    )

    wandb.log({"predictions sample": wandb.Table(dataframe=predictions_df)})

    LOGGER.info("Saving model to weights and biases...")
    tmpdir = TemporaryDirectory()
    model._save_pretrained(tmpdir.name)
    (Path(tmpdir.name) / "class_names.txt").write_text("\n".join(mlb.classes_))
    artifact = wandb.Artifact(
        argilla_dataset_name,
        type="model",
        description=f"model trained on {argilla_dataset_name} data",
    )
    artifact.add_dir(tmpdir.name)
    wandb.log_artifact(artifact)

    LOGGER.info("Model saved to weights and biases.")

    LOGGER.info("Script execution completed.")


if __name__ == "__main__":
    cli()
