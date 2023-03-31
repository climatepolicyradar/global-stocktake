.PHONY: install test

install:
	git init
	poetry install
	poetry run pre-commit install
	poetry run ipython kernel install --user

test: install
	poetry run python -m pytest -vvv

build:
	docker-compose build

up:
	docker-compose up

# needs explorer to be installed in the envirivonment this is run in
fossil-fuels:
	explorer gst -i ./concepts/fossil-fuels/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/fossil-fuels

technologies:
	explorer gst -i ./concepts/technologies/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies

greenhouse-gases:
	explorer gst -i ./concepts/greenhouse-gases/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/greenhouse-gases

concepts: fossil-fuels technologies greenhouse-gases