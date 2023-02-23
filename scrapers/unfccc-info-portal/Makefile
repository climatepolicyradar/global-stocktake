install:
	poetry install
	poetry run pre-commit install
	mkdir -p scraped/pdfs
	mkdir -p scraped/table_pages
	mkdir -p scraped/document_pages
	mkdir -p scraped/archive
	mkdir -p scraped/jsons
run:
	poetry run python src/main.py scrape_tables
	poetry run python src/main.py parse_tables
	poetry run python src/main.py scrape_pdfs
	poetry run python src/main.py scrape_document_pages
	poetry run python src/main.py parse_document_pages
	poetry run python src/main.py create-csv
	poetry run python src/main.py analysis-report
