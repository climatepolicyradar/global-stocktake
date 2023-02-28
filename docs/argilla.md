# Argilla

## Setup

See [docker-compose section in Argilla docs](https://docs.argilla.io/en/latest/getting_started/installation/deployments/docker_compose.html).

* To deploy: `docker-compose -f docker-compose.argilla.yml up -d` from the root of this repo
* To stop: `docker compose -f docker-compose.argilla.yml stop`

Two environment variables are important: `ARGILLA_API_KEY` and `ARGILLA_API_URL`. These are [used as defaults in `rg.init()`](https://docs.argilla.io/en/latest/reference/python/python_client.html#argilla.init).

## Deployment

Argilla is deployed on an EC2 instance in the Labs account using docker compose. You can log in to it using ec2 instance connect: `mssh <instance-name> region=eu-west-2`.

## Data import and export

See [notebooks/argilla](notebooks/argilla).

## User and Workspace Management

See [Argilla docs](https://docs.argilla.io/en/latest/getting_started/installation/configurations/user_management.html).

There are two workspaces set up: `gst` and `gst_dev`. The former is available to everyone, and the latter is intended for development and testing, and is only available to developers and data scientists.