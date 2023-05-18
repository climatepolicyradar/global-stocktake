.PHONY: install test concepts mitigation adaptation loss-and-damage vulnerable-groups renewables financial-flows equity-and-justice deforestation climate-related-hazards challenges-and-opportunities greenhouse-gases technologies fossil-fuels cop28 split_spans_csvs sync_concepts_with_s3
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
	explorer_merge GST -e ./concepts/fossil-fuels/output.xlsx -m ${SCRAPER_CSV_PATH}

technologies:
	explorer gst -i ./concepts/technologies/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies
	explorer_merge GST -e ./concepts/technologies/output.xlsx -m ${SCRAPER_CSV_PATH}

greenhouse-gases:
	explorer gst -i ./concepts/greenhouse-gases/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/greenhouse-gases
	explorer_merge GST -e ./concepts/greenhouse-gases/output.xlsx -m ${SCRAPER_CSV_PATH}

cop28:
	explorer gst -i ./concepts/5-COP28-GST-asks/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/5-COP28-GST-asks

challenges-and-opportunities:
	explorer gst -i ./concepts/challenges-and-opportunities/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/challenges-and-opportunities
	explorer_merge GST -e ./concepts/challenges-and-opportunities/output.xlsx -m ${SCRAPER_CSV_PATH}

climate-related-hazards:
	explorer gst -i ./concepts/climate-related-hazards/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/climate-related-hazards
	explorer_merge GST -e ./concepts/climate-related-hazards/output.xlsx -m ${SCRAPER_CSV_PATH}

deforestation:
	explorer gst -i ./concepts/deforestation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/deforestation
	explorer_merge GST -e ./concepts/deforestation/output.xlsx -m ${SCRAPER_CSV_PATH}

equity-and-justice:
	explorer gst -i ./concepts/equity-and-justice/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/equity-and-justice
	explorer_merge GST -e ./concepts/equity-and-justice/output.xlsx -m ${SCRAPER_CSV_PATH}

financial-flows:
	explorer gst -t -i ./concepts/financial-flows/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/financial-flows
	explorer_merge GST -e ./concepts/financial-flows/output.xlsx -m ${SCRAPER_CSV_PATH}

renewables:
	explorer gst -i ./concepts/renewables/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/renewables
	explorer_merge GST -e ./concepts/renewables/output.xlsx -m ${SCRAPER_CSV_PATH}

vulnerable-groups:
	explorer gst -i ./concepts/vulnerable-groups/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/vulnerable-groups
	explorer_merge GST -e ./concepts/vulnerable-groups/output.xlsx -m ${SCRAPER_CSV_PATH}

loss-and-damage:
	explorer_merge GST -e ./concepts/loss-and-damage/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer gst -i ./concepts/loss-and-damage/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/loss-and-damage

mitigation:
	explorer_merge GST -e ./concepts/mitigation/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer gst -i ./concepts/mitigation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/mitigation

adaptation:
	explorer_merge GST -e ./concepts/adaptation/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer gst -i ./concepts/adaptation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/adaptation

# split spans csvs into smaller chunks that can be pushed to git
split_spans_csvs:
	python src/data/split_spans_csvs.py

concepts: fossil-fuels technologies greenhouse-gases challenges-and-opportunities climate-related-hazards deforestation equity-and-justice financial-flows renewables vulnerable-groups cop28 loss-and-damage mitigation adaptation split_spans_csvs

sync_concepts_with_s3:
	aws s3 sync ./concepts s3://cpr-dataset-gst-concepts