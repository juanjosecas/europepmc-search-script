import requests
import json
import csv
import datetime
import time
import re
from collections import Counter
import pandas as pd
import argparse
import logging

# Logging system configuration
logging.basicConfig(filename='search_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Preprocessing Functions
def normalize_query(query):
    query = query.strip().lower()
    return query

def validate_query(query):
    if re.search(r'[^a-zA-Z0-9& ]', query):
        return False
    return True

# Main function to extract information from the API
def getInfo(results, output_format="csv", include_extra=False):
    hits = results["resultList"]["result"]
    
    if len(hits) == 0:
        logging.info("No records found in the search.")
        return  # Do not write to CSV if there is no data

    logging.info(f"Processing {len(hits)} results...")

    if include_extra:
        infos = ["isOpenAccess", "citedByCount", "id", "pmcid", "pmid", "authorString", "title", 
                 "journalTitle", "pubYear", "journalVolume", "pageInfo", "doi", "abstract", "hasFullText"]
    else:
        infos = ["isOpenAccess", "citedByCount", "id", "pmcid", "pmid", "authorString", "title", 
                 "journalTitle", "pubYear", "journalVolume", "pageInfo", "doi"]

    if output_format == "csv":
        outf_name = "records.csv"
        with open(outf_name, "a", newline='') as outf:
            writer = csv.writer(outf)
            # Only write the header if the file is empty
            if outf.tell() == 0:
                writer.writerow(infos)
            for hit in hits:
                ret_infos = [str(hit.get(info, "")) for info in infos]
                if any(ret_infos):  # Only write if there is valid data
                    writer.writerow(ret_infos)
        logging.info(f"Results saved to '{outf_name}'.")

    elif output_format == "json":
        outf_name = "records.json"
        with open(outf_name, "a") as outf:
            json.dump(hits, outf, indent=4)
        logging.info(f"Results saved to '{outf_name}'.")

    elif output_format == "excel":
        df = pd.DataFrame(hits)
        df.to_excel('records.xlsx', index=False)
        logging.info("Results exported to 'records.xlsx'.")

# Function to execute the search with pagination and error handling
def runSearch(url, data, output_format="csv", include_extra=False, retries=3):
    cursorMark = "*"
    has_more = True
    total_hits = 0
    attempt = 0

    try:
        while has_more:
            logging.info(f"Sending request to API with cursorMark: {cursorMark}...")
            try:
                data["cursorMark"] = cursorMark
                response = requests.get(url, params=data)
                
                # Detect rate limit
                if response.status_code == 429:
                    logging.warning("Rate limit exceeded. Waiting before retrying...")
                    retry_after = int(response.headers.get("Retry-After", 60))  # Wait for the suggested time or 60 seconds
                    time.sleep(retry_after)
                    continue  # Retry after waiting
                
                if response.status_code == 200:
                    logging.info("Request successful. Processing received data...")
                    results = json.loads(response.text)
                    cursorMark = results.get('nextCursorMark', None)
                    total_hits += len(results["resultList"]["result"])
                    getInfo(results, output_format, include_extra)
                    
                    # Delay between requests to avoid API saturation
                    time.sleep(2)
                    
                    if not cursorMark:
                        has_more = False
                else:
                    logging.error(f"Request error: {response.status_code}")
                    break
            except requests.exceptions.RequestException as e:
                logging.error(f"Connection error: {e}. Attempt {attempt+1}/{retries}.")
                attempt += 1
                if attempt > retries:
                    logging.error("Maximum number of retries reached. Aborting.")
                    break
                time.sleep(2**attempt)

    except KeyboardInterrupt:
        logging.warning("Process interrupted by the user. Exiting the program.")
        print("\nInterruption detected. Exiting the program...")

    logging.info(f"Search completed. Total records retrieved: {total_hits}")

# Function to handle command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Script to search articles in the European PMC API with multiple filters.")
    parser.add_argument('query_term', help='Search term (e.g., "cancer", "machine learning")')
    parser.add_argument('output_format', choices=['csv', 'json', 'excel'], default='csv', nargs='?', help='Output format (csv, json, excel)')
    parser.add_argument('--start_year', type=str, help='Start year of the search range (e.g., 2010)')
    parser.add_argument('--end_year', type=str, help='End year of the search range (e.g., 2021)')
    parser.add_argument('--article_type', type=str, help='Type of article (e.g., "research-article", "review")')
    parser.add_argument('--open_access', choices=['Y', 'N'], help='Filter by open access articles (Y/N)')
    parser.add_argument('--lang', type=str, help='Filter by article language (e.g., "eng" for English)')
    parser.add_argument('--include_extra', action='store_true', help='Include more information in the CSV (abstract, fullText, etc.)')
    return parser.parse_args()

# Main execution of the script
if __name__ == "__main__":
    args = parse_args()
    query = args.query_term
    output_format = args.output_format
    include_extra = args.include_extra

    # Normalize and validate the search term
    query = normalize_query(query)
    if not validate_query(query):
        logging.error(f"Invalid search term: {query}")
        exit()

    URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"

    logging.info(f"Building query for search term: '{query}'...")
    
    # Prepare the search data
    data_search = {
        "query": f"{query}",
        "resultType": "lite", 
        "pageSize": "1000",  # Maximum page size
        "sort": "",  # You can use "relevance", "date", etc.
        "format": "json",
    }

    # Add optional filter parameters if provided
    if args.start_year and args.end_year:
        data_search["pubYear"] = f"{args.start_year}:{args.end_year}"
        logging.info(f"Filtering by years: from {args.start_year} to {args.end_year}.")
    
    if args.article_type:
        data_search["articleType"] = args.article_type
        logging.info(f"Filtering by article type: {args.article_type}.")
    
    if args.open_access:
        data_search["isOpenAccess"] = args.open_access
        logging.info(f"Filtering by open access: {args.open_access}.")
    
    if args.lang:
        data_search["lang"] = args.lang
        logging.info(f"Filtering by language: {args.lang}.")

    now = datetime.datetime.now()
    logging.info(f"Search date and time: {now}")
    logging.info(f"Sending query to API with the following parameters: {data_search}")

    runSearch(URL, data_search, output_format, include_extra)
