import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX") # Your Google Custom Search Engine ID
# BING_API_KEY = os.getenv("BING_API_KEY") # Your Bing Search API Key (Temporarily disabled)

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
# BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search" # (Temporarily disabled)

# --- Functions ---

def google_search(query: str, api_key: str, cx: str, num_results: int = 10):
    """Performs a Google Custom Search."""
    if not api_key or not cx:
        print("Error: Google API Key or CX ID not found in environment variables.")
        return None

    params = {
        'key': api_key,
        'cx': cx,
        'q': query,
        'num': num_results
    }
    try:
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during Google Search API call: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from Google Search API.")
        print(f"Response text: {response.text[:500]}...") # Print first 500 chars
        return None

# def bing_search(query: str, api_key: str, num_results: int = 10):
#     """Performs a Bing Web Search. (Temporarily disabled)"""
#     if not api_key:
#         print("Error: Bing API Key not found in environment variables.")
#         return None
#
#     headers = {
#         'Ocp-Apim-Subscription-Key': api_key
#     }
#     params = {
#         'q': query,
#         'count': num_results,
#         'responseFilter': 'Webpages' # Focus on web results
#     }
#     try:
#         response = requests.get(BING_SEARCH_URL, headers=headers, params=params, timeout=10)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error during Bing Search API call: {e}")
#         return None
#     except json.JSONDecodeError:
#         print("Error: Could not decode JSON response from Bing Search API.")
#         print(f"Response text: {response.text[:500]}...") # Print first 500 chars
#         return None

def save_json(data, filename: str):
    """Saves data to a JSON file."""
    if data:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved results to {filename}")
        except IOError as e:
            print(f"Error saving file {filename}: {e}")
    else:
        print(f"No data to save for {filename}.")

def extract_urls_from_results(results_json: dict | None, num_urls: int) -> list[str]:
    """Extracts URLs from the Google results JSON dictionary."""
    urls = []
    if not results_json or not isinstance(results_json, dict) or "items" not in results_json:
        print("Warning: No 'items' found or invalid format in search results.")
        return []

    items = results_json.get("items", [])
    for item in items[:num_urls]: # Limit to the number we want to process
        link = item.get("link")
        if link:
            urls.append(link)
    # Keep print statement in the main pipeline script for better flow control
    # print(f"Extracted {len(urls)} URLs to potentially scrape.")
    return urls

def run_search(query: str, output_filename: str = "google_results.json", num_results: int = 10):
    """Runs the Google search and saves results to a file."""
    print(f"\n--- Running Search Phase for query: '{query}' ---")
    google_results = google_search(query, GOOGLE_API_KEY, GOOGLE_CX, num_results=num_results)
    if google_results:
        save_json(google_results, output_filename)
        print(f"Search results saved to {output_filename}")
        return True
    else:
        print("Search failed, results not saved.")
        return False

# --- Main Execution (for standalone testing) ---
if __name__ == "__main__":
    # Example usage when run directly
    test_query = "latest advancements in AI fairness"
    run_search(test_query)
    print("\nStandalone search_apis.py execution finished.")
