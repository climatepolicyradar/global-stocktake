import csv
import glob
import logging
from scrapy.http import HtmlResponse
import os
import json

def parse_tables():
    logger = logging.getLogger("gst-scraper")
    
    table_pages_folder = 'scraped/table_pages'
    json_folder = 'scraped/jsons'

    if not os.path.exists(table_pages_folder):
        raise FileNotFoundError(f"Directory '{table_pages_folder}' not found. Please run install as per README.")
    if not os.listdir(table_pages_folder):
        raise FileNotFoundError(f"Directory '{table_pages_folder}' is empty. Please run 'scrape_tables' command.")

    for file in os.listdir(table_pages_folder):
        if file.endswith(".html"):
            html_file = os.path.join(table_pages_folder, file)
            details = extract_table_details(html_file, logger)

            # Save the details as a JSON file per document
            for detail in details:
                # Take the PDF filename from the url
                pdf_filename = detail['pdf_link'].split('/')[-1]
                json_file = f"{json_folder}/{pdf_filename}.json"

                with open(json_file, "w") as f:
                    json.dump(detail, f)

def parse_document_pages():
    logger = logging.getLogger("gst-scraper")
    
    document_pages_folder = 'scraped/document_pages'
    json_folder = 'scraped/jsons'

    if not os.path.exists(document_pages_folder):
        raise FileNotFoundError(f"Directory '{document_pages_folder}' not found. Please run install as per README.")
    if not os.listdir(document_pages_folder):
        raise FileNotFoundError(f"Directory '{document_pages_folder}' is empty. Please run 'scrape_document_pages' command.")

    for file in os.listdir(document_pages_folder):
        if file.endswith(".html"):
            json_file = os.path.join(json_folder, file.replace('.html', '.json'))
            
            with open(json_file, 'r') as f:
                file_data = json.load(f)

            html_file = os.path.join(document_pages_folder, file)
            file_data = parse_document_page(html_file, file_data, logger)

            # Save the details back to the JSON file
            with open(json_file, "w") as f:
                json.dump(file_data, f)


def aggregate_to_csv():
    """Aggregate the JSON files into a single CSV file."""
    logger = logging.getLogger("gst-scraper")

    logger.info("Aggregating JSON files into CSV file")

    # Find all the JSON files in the table_pages/ directory
    json_files = glob.glob("scraped/jsons/*.json")

    # Grab the field names from the first json object keys
    with open(json_files[0], 'r') as f:
        data = json.load(f)
        fieldnames = list(data.keys())

    # Open the CSV file for writing
    with open('unfccc_files.csv', 'w', newline='') as csvfile:
        # Create a writer object
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        # Loop through the list of JSON files
        for filename in json_files:
            with open(filename, 'r') as f:
                # Load the JSON data from the file
                data = json.load(f)

                # Write the data json values to the CSV file
                writer.writerow(data)

def clean_scrapy_array(arr):
    """Given a list of strings, strip all whitespace characters and delete if empty, clean up characters"""
    arr = [item.strip() for item in arr]
    arr = [item for item in arr if item]
    arr = ["".join([char for char in t if char.isalnum() or char == " "]) for t in arr]
    return arr

def parse_document_page(html_file, file_data, logger):
    """Given a document HTML file, extract the topic list and the country and add to JSON file data as topics, party"""
    logger.info(f"Extracting details from document page: {html_file}")

    with open(html_file, 'r') as f:
        html_content = f.read()
    
    if not html_content:
        logger.warning(f"No HTML content found in file: {html_file}")
        return file_data
    
    response = HtmlResponse(url="", body=html_content, encoding='utf-8')
    country = response.css("div[class='field field--name-field-document-country field--type-termstore-entity-reference field--label-inline'] div[class='field--items'] ::text").getall()
    topics = response.css("div[class='field field--name-field-document-topic field--type-termstore-entity-reference field--label-inline'] div[class='field--items'] ::text").getall()

    country = clean_scrapy_array(country)
    topics = clean_scrapy_array(topics)

    file_data['party'] = ",".join(country)
    file_data['topics'] = ",".join(topics)
    return file_data

def extract_table_details(html_file, logger):
    """Given a table HTML_file, extract the details of each submission 
    and return a list of dictionaries containing the details.
    """
    logger.info(f"Extracting details from table page: {html_file}")

    with open(html_file, 'r') as f:
        html_content = f.read()

    if not html_content:
        logger.warning("No HTML content found in file: {html_file}")
        return []

    details = []
    response = HtmlResponse(url="", body=html_content, encoding='utf-8')
    for row in response.css("tbody > tr"):
        title = row.css(":nth-child(1) div ::text").get()
        title = title.strip().replace('\n', '') if title else ""

        theme = row.css(":nth-child(2) div ::text").get()
        theme = theme.strip().replace('\n', '') if theme else ""

        type = row.css(":nth-child(3) div ::text").get()
        type = type.strip().replace('\n', '') if type else ""

        author = row.css(":nth-child(4) div ::text").get()
        author = author.strip().replace('\n', '') if author else ""

        date = row.css(":nth-child(5) div time::attr(datetime)").get()
        date = date.strip().replace('\n', '') if date else ""

        link = row.css(":nth-child(6) a::attr(href)").get()
        link = link.strip().replace('\n', '') if link else ""

        pdf_links = []
        pdf_select = row.css(":nth-child(7) select")
        if pdf_select:
            pdf_options = pdf_select.css("option")

            logger.info(f"Found {len(pdf_options)-1} PDF links")

            for pdf_option in pdf_options:
                pdf_link = pdf_option.css("::attr(value)").get()

                # Get the text of the option as language
                language = pdf_option.css("::text").get()

                if pdf_link:
                    pdf_link = pdf_link.strip().replace('\n', '')
                    if pdf_link == "_none":
                        continue  # Skip the first empty option
                    pdf_links.append({ "language": language, "link": pdf_link })

        # One output per PDF file
        for pdf_link in pdf_links:
            logger.info(f"Extracted PDF link: {pdf_link['link']}")
            item = {
                "md5sum": "", 
                "title": title,
                "theme": theme,
                "type": type,
                "author": author,
                "author_type": "", 
                "date": date,
                "language": pdf_link['language'],
                "link": link,
                "pdf_link": pdf_link['link'],
                "validation_status": "Unvalidated",
                "data_error_type": "",
                "party": "",
                "translation": "",
                "version": "",
                "status": "",
                "source": "UNFCCC Information Portal"
            }

            details.append(item)

        logger.info(f"Extracted details from table row: {title}")
        logger.info(item)

    return details