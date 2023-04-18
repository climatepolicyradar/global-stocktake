.PHONY: install test
include .env

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

index_data:
	poetry run python -m src.opensearch.index_data ${DOCS_DIR_GST} ${SCRAPER_CSV_PATH} ./concepts -i global-stocktake

## Elastic Beanstalk
archive:
	git archive -v -o ebs_archive.zip --add-file=.env --format=zip HEAD

# needs explorer to be installed in the environment this is run in
fossil-fuels:
	explorer gst -i ./concepts/fossil-fuels/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/fossil-fuels

technologies:
	explorer gst -i ./concepts/technologies/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies

greenhouse-gases:
	explorer gst -i ./concepts/greenhouse-gases/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/greenhouse-gases

cop28:
	explorer gst -i ./concepts/5-COP28-GST-asks/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/5-COP28-GST-asks

best-practice:
	explorer gst -i ./concepts/best-practice/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/best-practice

climate-related-hazards:
	explorer gst -i ./concepts/climate-related-hazards/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/climate-related-hazards

deforestation:
	explorer gst -i ./concepts/deforestation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/deforestation

equity-and-justice:
	explorer gst -i ./concepts/equity-and-justice/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/equity-and-justice

financial-flows:
	explorer gst -i ./concepts/financial-flows/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/financial-flows

renewables:
	explorer gst -i ./concepts/renewables/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/renewables

vulnerable-groups:
	explorer gst -i ./concepts/vulnerable-groups/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/vulnerable-groups

concepts: fossil-fuels technologies greenhouse-gases best-practice climate-related-hazards deforestation equity-and-justice financial-flows renewables vulnerable-groups cop28