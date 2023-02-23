# UNFCCC Scraper

Scripts to pull out all the UNFCCC submission documents from the GST portal. Runs a pipeline that follows the following steps:
1. Download all the paginated table views enumerating all of the documents and their main metadata
2. Parse the downloaded HTML files to generate JSON objects (one per file) and an aggregated unfccc.csv file with file details and metadata
3. Download all the PDF files linked in the CSV file
4. Download all the document-specific pages linked in the CSV file
5. Parse the topics metadata for each document out of the downloaded document pages and update the CSV 

# Usage

Requires Poetry. 

Run `make install` to set up dependencies.

## Proxying

Currently, the document page scraper is set up to use ScrapeOps to bypass the more aggressive protection here. To activate the proxy, set the SCRAPEOPS_API_KEY variable in the dot env file. 

## Logging

If LOKI_URL is set in the .env file, the script will log to the given Loki instance. 