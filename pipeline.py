import os
import time
import argparse
import shutil # Import shutil for directory removal
from dotenv import load_dotenv

# Import the main run functions from each module
from search_apis import run_search
from scraper import run_scrape, RESULTS_FILE as SCRAPER_INPUT_FILE, OUTPUT_DIR as SCRAPER_OUTPUT_DIR
from parser import run_parse, HTML_DIR as PARSER_INPUT_DIR, OUTPUT_FILE as PARSER_OUTPUT_FILE
from summarizer import run_summarize, PARSED_CONTENT_FILE as SUMMARIZER_INPUT_FILE

# --- Configuration ---
load_dotenv() # Load environment variables from .env file (needed by imported modules)

# Pipeline Settings (can override module defaults if needed)
NUM_SEARCH_RESULTS_TO_REQUEST = 10 # How many results to ask Google for
MAX_URLS_TO_SCRAPE_PIPELINE = 5 # How many of the Google results to actually try scraping

# Define intermediate file/dir names consistently
SEARCH_RESULTS_FILENAME = "google_results.json"
SCRAPED_HTML_DIRNAME = "scraped_html"
PARSED_CONTENT_FILENAME = "parsed_content.json"

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full Search->Scrape->Parse->Summarize pipeline.")
    parser.add_argument("query", type=str, help="The search query.")
    args = parser.parse_args()

    start_time = time.time()
    print(f"=== Starting Full Pipeline for query: '{args.query}' ===")

    # === Stage 1: Search ===
    # Ensure the output filename matches what the scraper expects
    search_success = run_search(
        query=args.query,
        output_filename=SEARCH_RESULTS_FILENAME,
        num_results=NUM_SEARCH_RESULTS_TO_REQUEST
    )

    if not search_success:
        print("\nPipeline halted: Search phase failed.")
        exit()

    # === Stage 2: Scrape ===
    # Clear previous scrape results first
    if os.path.exists(SCRAPED_HTML_DIRNAME):
        try:
            shutil.rmtree(SCRAPED_HTML_DIRNAME)
            print(f"\nCleared previous scrape results directory: {SCRAPED_HTML_DIRNAME}")
        except OSError as e:
            print(f"\nError clearing directory {SCRAPED_HTML_DIRNAME}: {e}. Proceeding anyway.")

    # Ensure input/output match parser expectations and config
    scrape_success = run_scrape(
        input_results_file=SEARCH_RESULTS_FILENAME,
        output_html_dir=SCRAPED_HTML_DIRNAME,
        num_urls_to_scrape=MAX_URLS_TO_SCRAPE_PIPELINE
    )

    if not scrape_success:
        # Decide if we should halt or continue (maybe some files were scraped?)
        # For now, let's try parsing whatever might be there.
        print("\nWarning: Scrape phase completed but reported no successful saves. Attempting parse anyway.")
        # If you want to halt strictly:
        # print("\nPipeline halted: Scrape phase failed to save any files.")
        # exit()


    # === Stage 3: Parse ===
    # Ensure input/output match summarizer expectations
    parse_success = run_parse(
        input_html_dir=SCRAPED_HTML_DIRNAME,
        output_json_file=PARSED_CONTENT_FILENAME
    )

    if not parse_success:
        print("\nPipeline halted: Parse phase failed to produce output.")
        exit()

    # === Stage 4: Summarize ===
    # run_summarize prints the output directly
    run_summarize(
        query=args.query,
        input_parsed_file=PARSED_CONTENT_FILENAME
    )

    end_time = time.time()
    print(f"\n=== Pipeline Finished ===")
    print(f"Total execution time: {end_time - start_time:.2f} seconds.")
