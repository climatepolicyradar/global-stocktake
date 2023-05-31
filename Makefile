.PHONY: install test concepts adaptation barriers-and-challenges capacity-building climate-related-hazards deforestation equity-and-just-transition fossil-fuels good-practice-and-opportunities greenhouse-gases international-cooperation loss-and-damage mitigation renewables response-measures technologies-adaptation technologies-mitigation vulnerable-groups split_spans_csvs sync_concepts_with_s3 concepts_non_ml concepts_with_ml concepts_classifiers concepts
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
cop28:
	explorer gst -i ./concepts/5-COP28-GST-asks/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/5-COP28-GST-asks

adaptation:
	explorer gst -i ./concepts/adaptation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/adaptation

barriers-and-challenges:
	explorer gst -i ./concepts/barriers-and-challenges/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/barriers-and-challenges

capacity-building:
	explorer gst -i ./concepts/capacity-building/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/capacity-building

climate-related-hazards:
	explorer gst -i ./concepts/climate-related-hazards/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/climate-related-hazards

deforestation:
	explorer gst -i ./concepts/deforestation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/deforestation

equity-and-just-transition:
	explorer gst -i ./concepts/equity-and-just-transition/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/equity-and-just-transition

financial-flows:
	explorer gst -t -i ./concepts/financial-flows/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/financial-flows

fossil-fuels:
	explorer gst -i ./concepts/fossil-fuels/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/fossil-fuels

good-practice-and-opportunities:
	explorer gst -i ./concepts/good-practice-and-opportunities/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/good-practice-and-opportunities

greenhouse-gases:
	explorer gst -i ./concepts/greenhouse-gases/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/greenhouse-gases

international-cooperation:
	explorer gst -i ./concepts/international-cooperation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/international-cooperation

loss-and-damage:
	explorer gst -i ./concepts/loss-and-damage/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/loss-and-damage

mitigation:
	explorer gst -i ./concepts/mitigation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/mitigation

renewables:
	explorer gst -i ./concepts/renewables/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/renewables

response-measures:
	explorer gst -i ./concepts/response-measures/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/response-measures

technologies-adaptation:
	explorer gst -i ./concepts/technologies-br-adaptation-br/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies-br-adaptation-br

technologies-mitigation:
	explorer gst -i ./concepts/technologies-br-mitigation-br/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies-br-mitigation-br

vulnerable-groups:
	explorer gst -i ./concepts/vulnerable-groups/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/vulnerable-groups

train_sector_classifier:
	poetry run python classifiers/trainer.py --argilla-dataset-name sector-text-classifier

train_instruments_classifier:
	poetry run python classifiers/trainer.py --argilla-dataset-name policy-instrument-text-classifier

merge_metadata:
	explorer_merge GST -e ./concepts/adaptation/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/barriers-and-challenges/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/capacity-building/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/climate-related-hazards/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/deforestation/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/equity-and-just-transition/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/financial-flows/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/fossil-fuels/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/good-practice-and-opportunities/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/greenhouse-gases/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/international-cooperation/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/loss-and-damage/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/mitigation/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/renewables/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/technologies-br-adaptation-br/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/technologies-br-mitigation-br/output.xlsx -m ${SCRAPER_CSV_PATH}
	explorer_merge GST -e ./concepts/vulnerable-groups/output.xlsx -m ${SCRAPER_CSV_PATH}

# NOTE: these should be run against the *best* model artifact, not the latest
run_sector_classifier:
	poetry run python classifiers/run_on_full_dataset.py --wandb-artifact-name climatepolicyradar/sector-text-classifier/sector-text-classifier:latest --output-dir ./concepts/sectors

run_instruments_classifier:
	poetry run python classifiers/run_on_full_dataset.py --wandb-artifact-name climatepolicyradar/policy-instrument-text-classifier/policy-instrument-text-classifier:latest --output-dir ./concepts/policy-instruments

# split spans csvs into smaller chunks that can be pushed to git
split_spans_csvs:
	python src/data/split_spans_csvs.py

# TODO: split_spans_csvs doesn't work as results are in subdirectories
concepts_non_ml: adaptation barriers-and-challenges capacity-building climate-related-hazards deforestation equity-and-just-transition fossil-fuels good-practice-and-opportunities greenhouse-gases international-cooperation loss-and-damage mitigation renewables response-measures technologies-adaptation technologies-mitigation vulnerable-groups split_spans_csvs

concepts_with_ml: financial-flows split_spans_csvs 

concepts_classifiers: run_sector_classifier run_instruments_classifier split_spans_csvs

concepts: concepts_non_ml concepts_with_ml concepts_classifiers

sync_concepts_with_s3:
	aws s3 sync ./concepts s3://cpr-dataset-gst-concepts