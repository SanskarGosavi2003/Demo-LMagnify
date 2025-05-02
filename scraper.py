import json
import requests
import time
import os
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

# --- Configuration ---
USER_AGENT = "MyLocalSearchBot/1.0 (+http://example.com/bot-info)" # Define your bot's user agent
RESULTS_FILE = "google_results.json"
OUTPUT_DIR = "scraped_html"
REQUEST_TIMEOUT = 15 # Seconds
FETCH_DELAY = 1 # Seconds delay between requests to the same domain

# --- Functions ---

def load_urls_from_results(filename: str, num_urls: int = 3) -> list[str]:
    """Loads the top 'num_urls' URLs from the Google results JSON file."""
    urls = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            results = json.load(f)

        items = results.get("items", [])
        for item in items[:num_urls]:
            link = item.get("link")
            if link:
                urls.append(link)
        print(f"Loaded {len(urls)} URLs from {filename}")
        return urls
    except FileNotFoundError:
        print(f"Error: Results file not found at {filename}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading URLs: {e}")
        return []

def can_fetch_url(target_url: str, user_agent: str) -> bool:
    """Checks robots.txt to see if the user agent is allowed to fetch the URL."""
    parsed_url = urlparse(target_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print(f"Warning: Skipping invalid URL {target_url}")
        return False

    robots_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt")

    rp = RobotFileParser()
    # Fetch robots.txt content using requests with timeout
    try:
        print(f"Fetching robots.txt from: {robots_url}")
        robots_response = requests.get(robots_url, timeout=REQUEST_TIMEOUT, headers={'User-Agent': user_agent})
        robots_response.raise_for_status() # Check for HTTP errors

        # Parse the fetched content
        print(f"Parsing robots.txt content...")
        rp.parse(robots_response.text.splitlines())

        # Add a small delay after parsing
        time.sleep(0.5) # Shorter delay might be sufficient now

        # Check permission using the parsed data
        allowed = rp.can_fetch(user_agent, target_url)
        print(f"Robots.txt check for {target_url}: {'Allowed' if allowed else 'Disallowed'}")
        return allowed

    except requests.exceptions.Timeout:
        print(f"Warning: Timeout fetching robots.txt from {robots_url}. Assuming disallowed.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Warning: Error fetching robots.txt from {robots_url}: {e}. Assuming disallowed.")
        return False
    except Exception as e:
        # Catch potential parsing errors or other issues
        print(f"Warning: Could not process robots.txt for {robots_url}. Assuming disallowed. Error: {e}")
        return False

def fetch_html(url: str, user_agent: str) -> str | None:
    """Fetches the HTML content of a URL using the specified user agent."""
    headers = {
        'User-Agent': user_agent
    }
    try:
        print(f"Fetching HTML from: {url}")
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # Check if content type is HTML
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            print(f"Warning: Content type for {url} is not text/html ({content_type}). Skipping.")
            return None

        return response.text
    except requests.exceptions.Timeout:
        print(f"Error: Timeout occurred while fetching {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during fetch: {e}")
        return None

def save_html(html_content: str, filename: str, directory: str):
    """Saves HTML content to a file."""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            return

    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully saved HTML to {filepath}")
    except IOError as e:
        print(f"Error saving HTML to {filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during save: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting Phase 2: Web Scraping ---")

    target_urls = load_urls_from_results(RESULTS_FILE, num_urls=10) # Process all 10 results

    if not target_urls:
        print("No URLs loaded. Exiting.")
    else:
        fetched_count = 0
        # Simple domain-based delay tracking
        last_fetch_time = {}

        for i, url in enumerate(target_urls):
            print(f"\nProcessing URL {i+1}/{len(target_urls)}: {url}")

            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Apply delay if fetching from the same domain consecutively
            current_time = time.time()
            if domain in last_fetch_time:
                time_since_last = current_time - last_fetch_time[domain]
                if time_since_last < FETCH_DELAY:
                    sleep_time = FETCH_DELAY - time_since_last
                    print(f"Waiting {sleep_time:.2f}s before fetching from {domain} again...")
                    time.sleep(sleep_time)

            if can_fetch_url(url, USER_AGENT):
                html = fetch_html(url, USER_AGENT)
                last_fetch_time[domain] = time.time() # Update last fetch time for this domain

                if html:
                    # Create a safe filename from the URL (replace non-alphanumeric chars)
                    safe_filename = "".join(c if c.isalnum() else "_" for c in url) + ".html"
                    # Limit filename length if necessary
                    max_len = 100
                    safe_filename = safe_filename[-max_len:]

                    save_html(html, safe_filename, OUTPUT_DIR)
                    fetched_count += 1
            else:
                 last_fetch_time[domain] = time.time() # Still update time even if disallowed by robots

        # This block is now part of the run_scrape function below
        # print(f"\nScraping finished. Attempted {len(target_urls)} URLs, successfully fetched and saved {fetched_count}.")
        # return fetched_count > 0 # REMOVE THIS MISPLACED RETURN

# --- Main Execution (for standalone testing) ---
if __name__ == "__main__":
    print("--- Starting Standalone Scraper Execution ---")
    # Use default config values for standalone run
    success = run_scrape(RESULTS_FILE, OUTPUT_DIR, num_urls_to_scrape=3)
    if success:
        print("Standalone scraping completed successfully (at least one file saved).")
    else:
        print("Standalone scraping completed, but no files were saved (check errors or input file).")
    print("\n--- Standalone Scraper Finished ---")

def run_scrape(input_results_file: str, output_html_dir: str, num_urls_to_scrape: int):
    """Loads URLs, scrapes allowed ones, and saves HTML."""
    print(f"\n--- Running Scrape Phase ---")
    print(f"Input: {input_results_file}, Output Dir: {output_html_dir}, Max URLs: {num_urls_to_scrape}")

    # Ensure the output directory exists before attempting to save files
    os.makedirs(output_html_dir, exist_ok=True)

    target_urls = load_urls_from_results(input_results_file, num_urls=num_urls_to_scrape)

    if not target_urls:
        print("No URLs loaded from results file. Skipping scraping.")
        return False # Indicate failure or nothing to do

    fetched_count = 0
    last_fetch_time = {} # Domain-based delay tracking

    for i, url in enumerate(target_urls):
        print(f"Processing URL {i+1}/{len(target_urls)}: {url}")

        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not domain:
            print(" -> Skipping (invalid domain)")
            continue

        # Apply delay
        current_time = time.time()
        if domain in last_fetch_time:
            time_since_last = current_time - last_fetch_time[domain]
            if time_since_last < FETCH_DELAY:
                sleep_time = FETCH_DELAY - time_since_last
                time.sleep(sleep_time)

        last_fetch_time[domain] = time.time()

        if can_fetch_url(url, USER_AGENT):
            html = fetch_html(url, USER_AGENT)
            if html:
                safe_filename = "".join(c if c.isalnum() else "_" for c in url) + ".html"
                max_len = 100
                safe_filename = safe_filename[-max_len:]
                save_html(html, safe_filename, output_html_dir)
                fetched_count += 1
                print(f" -> Successfully scraped & saved.")
            else:
                 print(f" -> Failed to fetch HTML.")
        else:
            print(f" -> Skipped (disallowed by robots.txt).")

    # Add the summary print and return statement here, at the end of the function
    print(f"\nScraping finished for this run. Attempted {len(target_urls)} URLs, successfully fetched and saved {fetched_count}.")
    return fetched_count > 0 # Return True if at least one file was saved
