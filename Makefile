.PHONY: install test

install:
	git init
	poetry install
	poetry run pre-commit install

test: install
	poetry run python -m pytest -vvv

build:
	docker-compose build

up:
	docker-compose up