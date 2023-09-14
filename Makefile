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
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/5-COP28-GST-asks/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/5-COP28-GST-asks

adaptation:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/adaptation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/adaptation

barriers-and-challenges:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/barriers-and-challenges/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/barriers-and-challenges

capacity-building:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/capacity-building/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/capacity-building

climate-related-hazards:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/climate-related-hazards/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/climate-related-hazards

deforestation:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/deforestation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/deforestation

equity-and-just-transition:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/equity-and-just-transition/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/equity-and-just-transition

financial-flows:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -t -i ./concepts/financial-flows/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/financial-flows

fossil-fuels:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/fossil-fuels/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/fossil-fuels

good-practice-and-opportunities:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/good-practice-and-opportunities/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/good-practice-and-opportunities

greenhouse-gases:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/greenhouse-gases/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/greenhouse-gases

international-cooperation:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/international-cooperation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/international-cooperation

loss-and-damage:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/loss-and-damage/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/loss-and-damage

mitigation:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/mitigation/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/mitigation

renewables:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/renewables/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/renewables

response-measures:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/response-measures/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/response-measures

technologies-adaptation:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/technologies-br-adaptation-br/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies-br-adaptation-br

technologies-mitigation:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/technologies-br-mitigation-br/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/technologies-br-mitigation-br

vulnerable-groups:
	explorer gst --spans-csv-filename ${SPANS_CSV_FILENAME} -i ./concepts/vulnerable-groups/input.xlsx -d ${DOCS_DIR_GST} -o ./concepts/vulnerable-groups

train_sector_classifier:
	poetry run python classifiers/trainer.py --argilla-dataset-name sector-text-classifier

train_instruments_classifier:
	poetry run python classifiers/trainer.py --argilla-dataset-name policy-instrument-text-classifier

# NOTE: these should be run against the *best* model artifact, not the latest
run_sector_classifier:
	poetry run python classifiers/run_on_full_dataset.py --spans-csv-filename ${SPANS_CSV_FILENAME} --wandb-artifact-name climatepolicyradar/sector-text-classifier/sector-text-classifier:latest --output-dir ./concepts/sectors

run_instruments_classifier:
	poetry run python classifiers/run_on_full_dataset.py --spans-csv-filename ${SPANS_CSV_FILENAME} --wandb-artifact-name climatepolicyradar/policy-instrument-text-classifier/policy-instrument-text-classifier:latest --output-dir ./concepts/policy-instruments

# split spans csvs into smaller chunks that can be pushed to git
split_spans_csvs:
	python src/data/split_spans_csvs.py ${SPANS_CSV_FILENAME}

# TODO: split_spans_csvs doesn't work as results are in subdirectories
concepts_non_ml: adaptation barriers-and-challenges capacity-building climate-related-hazards deforestation equity-and-just-transition fossil-fuels good-practice-and-opportunities greenhouse-gases international-cooperation loss-and-damage mitigation renewables response-measures technologies-adaptation technologies-mitigation vulnerable-groups

concepts_with_ml: financial-flows

concepts_classifiers: run_sector_classifier run_instruments_classifier

concepts: concepts_non_ml concepts_with_ml concepts_classifiers #split_spans_csvs

sync_concepts_to_s3:
	aws s3 sync ./concepts s3://cpr-dataset-gst-concepts

sync_concepts_from_s3:
	aws s3 sync s3://cpr-dataset-gst-concepts ./concepts