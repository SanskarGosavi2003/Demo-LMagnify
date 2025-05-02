# Local Search and Summarization Pipeline

## Overview

This pipeline automates the process of searching the web for a given query, scraping relevant web pages, extracting their textual content, and finally generating a concise summary based on the collected information using a Large Language Model (LLM).

It's designed to provide quick answers to questions by leveraging web search results and AI summarization.

## Prerequisites

1.  **Python:** Python 3.x installed.
2.  **Pip:** Python package installer.
3.  **API Keys:** You need API keys for:
    *   **Google Custom Search Engine (CSE):** To perform web searches.
    *   **Google AI (Gemini):** To generate the final summary.
4.  **`.env` File:** Create a `.env` file in the project root directory to store your API keys securely. It should contain:
    ```env
    GOOGLE_API_KEY=YOUR_GOOGLE_CSE_API_KEY
    GOOGLE_CSE_ID=YOUR_GOOGLE_CSE_ID
    GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    # Optional: Define a User-Agent for scraping
    # USER_AGENT=YourCustomUserAgent/1.0
    ```
5.  **Python Libraries:** Install the required libraries. While a `requirements.txt` is recommended, you'll likely need:
    ```bash
    pip install python-dotenv requests google-api-python-client beautifulsoup4 google-generativeai
    ```
    *(Note: `beautifulsoup4` is assumed for parsing; the exact libraries are defined in the individual Python scripts.)*

## Configuration

*   **API Keys:** Set in the `.env` file (see Prerequisites).
*   **Pipeline Settings (in `pipeline.py`):**
    *   `NUM_SEARCH_RESULTS_TO_REQUEST`: How many search results to fetch from Google CSE.
    *   `MAX_URLS_TO_SCRAPE_PIPELINE`: How many of the top search results to attempt scraping.
*   **Intermediate Files/Directories (defined in `pipeline.py` and module constants):**
    *   `google_results.json`: Stores the raw results from the Google CSE API.
    *   `scraped_html/`: Directory where fetched HTML files are saved.
    *   `parsed_content.json`: Stores the extracted text content from the scraped HTML files.

## Workflow Details

The pipeline executes in sequential stages, managed by `pipeline.py`:

1.  **Initialization:**
    *   Takes the user's search query as a command-line argument.
    *   Loads API keys and other environment variables from the `.env` file using `dotenv`.
    *   Sets up pipeline configuration constants.

2.  **Stage 1: Search (`search_apis.run_search`)**
    *   **Input:** User query, `NUM_SEARCH_RESULTS_TO_REQUEST`.
    *   **Process:** Uses the Google Custom Search API (`googleapiclient`) with the provided `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` to find web pages relevant to the query.
    *   **Output:** Saves the raw JSON response from the API into `google_results.json`. The pipeline checks if the search was successful before proceeding.

3.  **Stage 2: Scrape (`scraper.run_scrape`)**
    *   **Input:** `google_results.json`, `MAX_URLS_TO_SCRAPE_PIPELINE`, output directory name (`scraped_html`).
    *   **Process:**
        *   Clears the `scraped_html/` directory if it exists from a previous run.
        *   Ensures the `scraped_html/` directory exists (creates it if needed).
        *   Reads `google_results.json` and extracts the `link` field from the top `MAX_URLS_TO_SCRAPE_PIPELINE` items.
        *   For each URL:
            *   Fetches the website's `robots.txt` file to check if scraping is permitted for the configured `USER_AGENT` (or a default one).
            *   If allowed, uses the `requests` library to download the HTML content of the page.
            *   Saves the raw HTML content into a file within the `scraped_html/` directory. The filename is generated based on the URL to avoid collisions.
    *   **Output:** HTML files stored in the `scraped_html/` directory. Reports the number of successfully scraped URLs. It proceeds even if some URLs fail or are skipped.

4.  **Stage 3: Parse (`parser.run_parse`)**
    *   **Input:** Input directory name (`scraped_html`), output filename (`parsed_content.json`).
    *   **Process:**
        *   Scans the `scraped_html/` directory for `.html` files.
        *   For each HTML file:
            *   Uses a library like `BeautifulSoup` to parse the HTML structure.
            *   Extracts the main textual content, likely attempting to ignore scripts, styles, navigation, and other non-primary content elements.
            *   Stores the extracted text associated with its source filename.
    *   **Output:** Creates `parsed_content.json`, containing a JSON object mapping the source HTML filenames (derived from URLs) to their extracted text content. The pipeline halts if no content is successfully parsed (e.g., if the `scraped_html` directory was empty or parsing failed for all files).

5.  **Stage 4: Summarize (`summarizer.run_summarize`)**
    *   **Input:** Input filename (`parsed_content.json`), original user query.
    *   **Process:**
        *   Loads the extracted text data from `parsed_content.json`.
        *   Concatenates the text content from all successfully parsed files.
        *   Constructs a prompt for the Gemini LLM (`google.generativeai`). This prompt typically includes the concatenated text and the original user query, asking the model to generate a summary relevant to the query.
        *   Uses the `GEMINI_API_KEY` to send the prompt to the Gemini API.
        *   Streams the generated summary response directly to the console.
    *   **Output:** Prints the final summary to the standard output.

6.  **Finalization:**
    *   Calculates and prints the total execution time of the pipeline.

## How to Run

1.  Ensure all prerequisites are met and the `.env` file is correctly configured.
2.  Open your terminal in the project's root directory.
3.  Run the pipeline script with your query as a command-line argument:

    ```bash
    python pipeline.py "Your search query goes here"
    ```

    Example:
    ```bash
    python pipeline.py "What are the benefits of hydration?"
    ```

## Error Handling & Edge Cases

*   The pipeline includes checks at the end of the Search, Scrape, and Parse stages. If a critical stage fails (e.g., Search fails, or Parse produces no output), the pipeline will print an error message and halt execution.
*   The Scraper respects `robots.txt` directives. If target websites disallow scraping, their URLs will be skipped.
*   If the Search phase yields results that are all disallowed by `robots.txt` or otherwise fail to scrape, the Parse phase might receive an empty input directory. The pipeline now handles this by creating the directory but parsing 0 files, leading to the Parse phase failing gracefully and halting the pipeline as expected.
