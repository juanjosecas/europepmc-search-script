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

# Function to display quick statistics
def display_statistics(results):
    if not results:
        print("\nNo results to display statistics.")
        logging.info("No results to display statistics.")
        return
    
    print("\n" + "="*60)
    print("QUICK STATISTICS")
    print("="*60)
    
    total_results = len(results)
    print(f"\nTotal Results: {total_results}")
    
    # Year distribution
    years = [hit.get('pubYear', 'Unknown') for hit in results]
    year_counts = Counter(years)
    print("\n--- Year Distribution (Top 10) ---")
    for year, count in year_counts.most_common(10):
        percentage = (count / total_results) * 100
        print(f"  {year}: {count} ({percentage:.1f}%)")
    
    # Open access statistics
    open_access_counts = Counter([hit.get('isOpenAccess', 'Unknown') for hit in results])
    print("\n--- Open Access Statistics ---")
    for status, count in open_access_counts.items():
        percentage = (count / total_results) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    # Journal distribution
    journals = [hit.get('journalTitle', 'Unknown') for hit in results]
    journal_counts = Counter(journals)
    print("\n--- Top 10 Journals ---")
    for journal, count in journal_counts.most_common(10):
        percentage = (count / total_results) * 100
        print(f"  {journal}: {count} ({percentage:.1f}%)")
    
    # Citation statistics
    citations = []
    for hit in results:
        try:
            cite_count = hit.get('citedByCount')
            if cite_count is not None:
                # Try to convert to integer or float
                if isinstance(cite_count, (int, float)):
                    citations.append(int(cite_count))
                elif isinstance(cite_count, str):
                    # Handle string representations of numbers
                    citations.append(int(float(cite_count)))
        except (ValueError, TypeError):
            continue
    
    if citations:
        avg_citations = sum(citations) / len(citations)
        max_citations = max(citations)
        print("\n--- Citation Statistics ---")
        print(f"  Average citations: {avg_citations:.1f}")
        print(f"  Maximum citations: {max_citations}")
        print(f"  Total citations: {sum(citations)}")
    
    print("\n" + "="*60 + "\n")
    logging.info(f"Statistics displayed for {total_results} results.")

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

    try:
        if output_format == "csv":
            outf_name = "records.csv"
            with open(outf_name, "a", newline='', encoding='utf-8') as outf:
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
            with open(outf_name, "a", encoding='utf-8') as outf:
                json.dump(hits, outf, indent=4, ensure_ascii=False)
            logging.info(f"Results saved to '{outf_name}'.")

        elif output_format == "excel":
            df = pd.DataFrame(hits)
            df.to_excel('records.xlsx', index=False)
            logging.info("Results exported to 'records.xlsx'.")
    except IOError as e:
        logging.error(f"Error writing to file: {e}")
        print(f"Error: Could not write results to file: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while saving results: {e}")
        print(f"Error: Could not save results: {e}")

# Function to execute the search with pagination and error handling
def runSearch(url, data, output_format="csv", include_extra=False, retries=3, timeout=30, max_results=None, stats_only=False):
    cursorMark = "*"
    has_more = True
    total_hits = 0
    attempt = 0
    all_results = [] if stats_only else None

    try:
        while has_more:
            logging.info(f"Sending request to API with cursorMark: {cursorMark}...")
            try:
                data["cursorMark"] = cursorMark
                response = requests.get(url, params=data, timeout=timeout)
                
                # Reset attempt counter on successful connection
                attempt = 0
                
                # Detect rate limit
                if response.status_code == 429:
                    logging.warning("Rate limit exceeded. Waiting before retrying...")
                    retry_after = int(response.headers.get("Retry-After", 60))  # Wait for the suggested time or 60 seconds
                    time.sleep(retry_after)
                    continue  # Retry after waiting
                
                if response.status_code == 200:
                    logging.info("Request successful. Processing received data...")
                    try:
                        results = json.loads(response.text)
                        
                        # Validate API response structure
                        if "resultList" not in results or "result" not in results["resultList"]:
                            logging.error("Invalid API response structure. Missing 'resultList' or 'result' fields.")
                            break
                        
                        current_hits = results["resultList"]["result"]
                        total_hits += len(current_hits)
                        
                        if stats_only:
                            all_results.extend(current_hits)
                        else:
                            getInfo(results, output_format, include_extra)
                        
                        cursorMark = results.get('nextCursorMark', None)
                        
                        # Check if max_results limit is reached
                        if max_results and total_hits >= max_results:
                            logging.info(f"Maximum results limit ({max_results}) reached. Stopping search.")
                            has_more = False
                        elif not cursorMark:
                            has_more = False
                        else:
                            # Delay between requests to avoid API saturation
                            time.sleep(2)
                            
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding JSON response: {e}")
                        break
                    except KeyError as e:
                        logging.error(f"Missing expected key in API response: {e}")
                        break
                        
                elif response.status_code == 400:
                    logging.error(f"Bad request (400): Invalid query parameters. Response: {response.text[:200]}")
                    break
                elif response.status_code == 404:
                    logging.error("API endpoint not found (404). Please check the URL.")
                    break
                elif response.status_code >= 500:
                    logging.error(f"Server error ({response.status_code}). The API may be temporarily unavailable.")
                    attempt += 1
                    if attempt > retries:
                        logging.error("Maximum number of retries reached due to server errors. Aborting.")
                        break
                    wait_time = min(2**attempt, 60)  # Cap wait time at 60 seconds
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Request error: {response.status_code} - {response.text[:200]}")
                    break
                    
            except requests.exceptions.Timeout as e:
                logging.error(f"Request timeout after {timeout} seconds: {e}. Attempt {attempt+1}/{retries}.")
                attempt += 1
                if attempt > retries:
                    logging.error("Maximum number of retries reached due to timeouts. Aborting.")
                    break
                wait_time = min(2**attempt, 60)
                time.sleep(wait_time)
            except requests.exceptions.ConnectionError as e:
                logging.error(f"Connection error: {e}. Attempt {attempt+1}/{retries}.")
                attempt += 1
                if attempt > retries:
                    logging.error("Maximum number of retries reached due to connection errors. Aborting.")
                    break
                wait_time = min(2**attempt, 60)
                time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: {e}. Attempt {attempt+1}/{retries}.")
                attempt += 1
                if attempt > retries:
                    logging.error("Maximum number of retries reached. Aborting.")
                    break
                wait_time = min(2**attempt, 60)
                time.sleep(wait_time)

    except KeyboardInterrupt:
        logging.warning("Process interrupted by the user. Exiting the program.")
        print("\nInterruption detected. Exiting the program...")
    except Exception as e:
        logging.error(f"Unexpected error during search: {e}")
        print(f"An unexpected error occurred: {e}")

    logging.info(f"Search completed. Total records retrieved: {total_hits}")
    
    if stats_only:
        return all_results
    return None

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
    parser.add_argument('--page_size', type=int, default=1000, help='Number of results per page (default: 1000, max: 1000)')
    parser.add_argument('--sort', type=str, choices=['', 'relevance', 'date', 'cited'], default='', 
                        help='Sort results by relevance, date, or citation count')
    parser.add_argument('--result_type', type=str, choices=['lite', 'core'], default='lite',
                        help='Result type: lite (basic fields) or core (full details)')
    parser.add_argument('--synonym', choices=['true', 'false'], default='false',
                        help='Enable synonym expansion in search (true/false)')
    parser.add_argument('--max_results', type=int, help='Maximum number of results to retrieve (optional)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retry attempts for failed requests (default: 3)')
    parser.add_argument('--stats', action='store_true', help='Display quick statistics instead of downloading all data')
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
        print(f"Error: Invalid search term '{query}'. Please use only alphanumeric characters and spaces.")
        exit(1)

    URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"

    logging.info(f"Building query for search term: '{query}'...")
    
    # Validate page_size
    if args.page_size < 1 or args.page_size > 1000:
        logging.error(f"Invalid page size: {args.page_size}. Must be between 1 and 1000.")
        print(f"Error: Page size must be between 1 and 1000.")
        exit(1)
    
    # Prepare the search data
    data_search = {
        "query": f"{query}",
        "resultType": args.result_type, 
        "pageSize": str(args.page_size),
        "sort": args.sort,
        "format": "json",
        "synonym": args.synonym,
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

    # Run search with statistics option if requested
    if args.stats:
        print(f"\nFetching results for '{query}' to display statistics...")
        print("This may take a moment depending on the number of results...")
        results = runSearch(URL, data_search, output_format, include_extra, 
                          retries=args.retries, timeout=args.timeout, 
                          max_results=args.max_results, stats_only=True)
        if results:
            display_statistics(results)
    else:
        runSearch(URL, data_search, output_format, include_extra, 
                 retries=args.retries, timeout=args.timeout, max_results=args.max_results)
