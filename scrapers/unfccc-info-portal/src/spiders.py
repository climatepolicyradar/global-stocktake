import csv
import datetime
import glob
import hashlib
import json
import logging
import os
from urllib.parse import urlencode
import scrapy

MAX_RETRIES = 3

class UNFCCCSpider(scrapy.Spider):
    """Scrapy spider for downloading all pages of the UNFCCC table of submissions.
    
    The spider starts at the information portal home page and extracts the URL of the last page from the paginated table.

    It then creates a list of URLs for all pages and yields a request for each page.

    Each page parse checks to see if the scraping protection has been triggered. In testing, if it gets triggered 3 or more times
    it remains blocked so there's no point continuing until a few minutes have elapsed or a new IP address is used. The site 
    also requires a user-agent header and uses this in the scraping protection, so changing that may also help.

    The spider saves each page to the scraped/table_pages directory as HTML files. Subsequent processing of these files is
    performed separately to prevent unnecessary re-downloading of the pages.
    """

    name = "unfccc"
    start_urls = [
        'https://unfccc.int/topics/global-stocktake/information-portal',
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gst_logger = logging.getLogger('gst-scraper')

    def parse(self, response):
        # Get the href attribute from the last page link
        last_page_url = response.css(".pager__item.pager__item--last a::attr(href)").get()

        if last_page_url is None:
            raise RuntimeError("Unable to find last page link")
    
        # Extract the number of pages from the last page link
        last_page_number = int(last_page_url.split("&page=")[1])
        if last_page_number < 1 or last_page_number > 1000:
            raise RuntimeError(f"Last page number is not in expected range: {last_page_number}")
        
        # Create a list of URLs for all pages
        pages = [f"https://unfccc.int/topics/global-stocktake/information-portal?page={i}" for i in range(last_page_number + 1)]

        # Yield a request for each page
        for page in pages:
            yield response.follow(page, self.parse_page)

    def parse_page(self, response):
        if "Request unsuccessful" in response.text:

            # Check if the maximum number of retries has been reached
            retries = response.meta.get('retry_times', 0)

            if retries < MAX_RETRIES:
                retries += 1
                yield response.follow(response.url, self.parse_page, dont_filter=True,
                                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'},
                                    meta={'retry_times': retries})
            else:
                # If the maximum retries has been reached, log a message and skip the page
                self.gst_logger.warning(f"Failed to download page {response.url} after {MAX_RETRIES} retries")
        else:
            # Save each HTML page to disk
            filename = f"./scraped/table_pages/page_{response.url.split('=')[-1]}.html"

            # Check if the file already exists
            if os.path.exists(filename):
                self.gst_logger.warning(f"File already exists: {filename}. Copying to archive directory.")
                # Add date to filename
                date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                archive_filename = f"./scraped/archive/page_{response.url.split('=')[-1]}-{date_str}.html"

                # Move the file to the archive directory   
                os.rename(filename, archive_filename)

            try:
                with open(filename, "wb") as f:
                    f.write(response.body)
            except Exception as e:
                self.gst_logger.error(f"Error saving file {filename}: {e}")

class PdfSpider(scrapy.Spider):
    """Scrapy spider for downloading all PDFs from the UNFCCC table of submissions. It walks the saved CSV file and yields a request for each PDF link.
    
    Can only be run when the UNFCCCSpider has been run and the CSV file has been created - see README.md for details.
    """
    name = "pdf_spider"

    custom_settings = {
        'DOWNLOAD_DELAY': 0.5
        }
    
    def start_requests(self):
        # Check if the json files exist
        if not os.path.exists("scraped/jsons") or len(os.listdir("scraped/jsons")) == 0:
            raise FileNotFoundError("JSON files not found. See README for run info.")

        # Open up each JSON file and yield a request for each PDF link
        json_files = glob.glob("scraped/jsons/*.json")

        for json_file in json_files:
            with open(json_file, 'r') as json_file:
                data = json.load(json_file)

                # Check JSON includes columns pdf_link and filename
                if 'pdf_link' not in data:
                    raise ValueError("JSON file does not contain PDF link.")

                pdf_link = data['pdf_link']
                yield scrapy.Request(pdf_link, self.parse, meta={'filename': os.path.basename(pdf_link)}, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36', 
                    }, 
                    dont_filter=True)

    def parse(self, response):
        if response.status != 200:
            raise RuntimeError(f"Request for {filename} returned status code {response.status}")
        
        # Extract the filename from the meta data
        filename = response.meta['filename']

        # Check if the file already exists
        if os.path.exists(f'scraped/pdfs/{filename}'):
            self.logger.warning(f"File already exists: {filename}. Copying to archive directory.")
            # Add date to filename
            date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            archive_filename = f"./scraped/archive/{filename}-{date_str}.pdf"
            # Move the file to the archive directory
            os.rename(f'scraped/pdfs/{filename}', archive_filename)

        # Save the PDF to disk
        with open(f'scraped/pdfs/{filename}', 'wb') as f:
            f.write(response.body)

        # Add the md5 sum to the json
        document_md5sum = hashlib.md5(response.body).hexdigest()
        json_filename = f'scraped/pdfs/{filename}.json'
        with open(json_filename, 'r') as json_file:
            data = json.load(json_file)
            data['md5sum'] = document_md5sum

            # Save the updated JSON file
            with open(json_filename, 'w') as json_file:
                json.dump(data, json_file)
    

class DocumentPageSpider(scrapy.Spider):
    """Scrapy spider for downloading all the individual document pages from the UNFCCC table of submissions. It walks the saved CSV file and yields a request for each document page link.
    The main thing we care about on this page is the topics list, which is the only additional metadata available not on the main table. 
    """

    name = "unfccc-documents-pages"
    scrape_ops_key = None

    # The scraper protection seems much more aggressive on the document pages, so we need to slow down the requests
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_DEBUG': True,
        'AUTOTHROTTLE_START_DELAY': 2,

        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        }
    }

    def __init__(self, scrape_ops_key=None, **kwargs):
        self.scrape_ops_key = scrape_ops_key
        super().__init__(**kwargs)

    def get_proxy_url(self, url):
        if self.scrape_ops_key is None:
            return url

        payload = {'api_key': self.scrape_ops_key, 'url': url}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        print(proxy_url)
        return proxy_url

    def start_requests(self):
        # Open up each JSON file and yield a request for each PDF link
        json_files = glob.glob("scraped/jsons/*.json")

        for json_file in json_files:
            with open(json_file, 'r') as json_file:
                data = json.load(json_file)

                # Yield a request for document page link
                link = f"https://unfccc.int{data['link']}"

                pdf_filename = data['pdf_link'].split('/')[-1]
                filename = f"{pdf_filename}.html"

                yield scrapy.Request(self.get_proxy_url(link), self.parse, meta={'filename': filename}, 
                    dont_filter=True)
                
    def parse(self, response):        
        # Extract the filename from the meta data
        filename = response.meta['filename']

        # Check if the file already exists
        if os.path.exists(f'scraped/document_pages/{filename}'):
            self.logger.warning(f"File already exists: {filename}. Copying to archive directory.")
            # Add date to filename
            date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            archive_filename = f"./scraped/archive/{filename}-{date_str}.pdf"
            # Move the file to the archive directory
            os.rename(f'scraped/document_pages/{filename}', archive_filename)

        # Save the PDF to disk
        with open(f'scraped/document_pages/{filename}', 'wb') as f:
            f.write(response.body)

    def parse_page(self, response):
        if "Request unsuccessful" in response.text:

            # Check if the maximum number of retries has been reached
            retries = response.meta.get('retry_times', 0)

            if retries < MAX_RETRIES:
                retries += 1
                yield response.follow(response.url, self.parse_page, dont_filter=True,
                                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'},
                                    meta={'retry_times': retries})
            else:
                # If the maximum retries has been reached, log a message and skip the page
                self.logger.warning(f"Failed to download page {response.url} after {MAX_RETRIES} retries")
        else:
            # Save each HTML page to disk
            filename = f"./scraped/document_pages/page_{response.url.split('=')[-1]}.html"

            # Check if the file already exists
            if os.path.exists(filename):
                self.logger.warning(f"File already exists: {filename}. Copying to archive directory.")
                # Add date to filename
                date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"./scraped/archive/page_{response.url.split('=')[-1]}-{date_str}.html"

            try:
                with open(filename, "wb") as f:
                    f.write(response.body)
            except Exception as e:
                self.logger.error(f"Error saving file {filename}: {e}")

    def process_request(self, request, spider):
        # Add a small delay in the requests
        import time
        time.sleep(0.5)
        return None