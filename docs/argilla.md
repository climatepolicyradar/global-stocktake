# Argilla

## Deployment

See [docker-compose section in Argilla docs](https://docs.argilla.io/en/latest/getting_started/installation/deployments/docker_compose.html).

* To deploy: `docker-compose -f docker-compose.argilla.yml up -d` from the root of this repo
* To stop: `docker compose -f docker-compose.argilla.yml stop`

## Data import and export

See [notebooks/argilla](notebooks/argilla).

## User and Workspace Management

See [Argilla docs](https://docs.argilla.io/en/latest/getting_started/installation/configurations/user_management.html).

There are two workspaces set up: `gst` and `gst_dev`. The former is available to everyone, and the latter is intended for development and testing, and is only available to developers and data scientists.