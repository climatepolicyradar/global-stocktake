from spiders import UNFCCCSpider, PdfSpider, DocumentPageSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from processing import parse_tables, parse_document_pages, aggregate_to_csv
import logging
import logging_loki
from dotenv import load_dotenv
import os
import argparse

def scrape_tables():
    process = CrawlerProcess()
    process.crawl(UNFCCCSpider)
    process.start()

def scrape_pdfs():
    process = CrawlerProcess()
    process.crawl(PdfSpider)
    process.start()

def scrape_document_pages():
    process = CrawlerProcess()
    process.crawl(DocumentPageSpider, scrape_ops_key=os.getenv('SCRAPEOPS_API_KEY'))
    process.start()

def analysis_report():
    logger = logging.getLogger("gst-scraper")
    logger.info("Analysis report to be implemented.")

if __name__ == "__main__":
    # Check directory structure
    if not os.path.exists('scraped'):
        raise FileNotFoundError("Directory 'scraped' not found. Please run install as per README.")

    # Load environment variables
    load_dotenv()

    logger = logging.getLogger("gst-scraper")

    # If loki_url is set,
    #  configure logging to send to Loki
    if os.getenv('LOKI_URL'):
        logging_loki.emitter.LokiEmitter.level_tag = "level"
        handler = logging_loki.LokiHandler(
            url=os.getenv('LOKI_URL'),
            version="1",
            tags={"app": "gst-scraper"},
        )
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog="gst-scraper",
        description="Scrape the UNFCCC Global Stocktake Information Portal"
    )
    parser.add_argument('command', 
                        help="""Command to run. 
                        'scrape_tables' runs the spider to scrape the table of submissions.
                        'parse_tables' parses the scraped HTML files and saves the results to JSON and CSV files.
                        'scrape_document_pages' runs the spider to scrape the document pages.
                        'parse_document_pages' parses the scraped HTML document files and saves the results to JSON  files.
                        'scrape_pdfs' runs the spider to scrape the PDFs.
                        'analysis-report' runs the analysis report.                        
                        """, 
                        choices=[
                                 'scrape_tables', 
                                 'parse_tables',
                                 'scrape_pdfs',
                                 'scrape_document_pages',
                                 'parse_document_pages',
                                 'create-csv', 
                                 'analysis-report'
                                 ]
                        )
    args = parser.parse_args()

    if args.command == 'all':
        scrape_tables()
        parse_tables()
        scrape_pdfs()
        scrape_document_pages()
        aggregate_to_csv()
        analysis_report()
    elif args.command == 'scrape_tables':
        scrape_tables()
    elif args.command == 'parse_tables':
        parse_tables()
    elif args.command == 'scrape_pdfs':
        scrape_pdfs()
    elif args.command == 'scrape_document_pages':
        scrape_document_pages()
    elif args.command == 'parse_document_pages':
        parse_document_pages()
    elif args.command == 'create-csv':
        aggregate_to_csv()
    elif args.command == 'analysis-report':
        analysis_report()
