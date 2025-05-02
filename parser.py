import os
import json
from bs4 import BeautifulSoup

# --- Configuration ---
HTML_DIR = "scraped_html"
OUTPUT_FILE = "parsed_content.json"

# --- Functions ---

def list_html_files(directory: str) -> list[str]:
    """Lists all .html files in the specified directory."""
    html_files = []
    if not os.path.isdir(directory):
        print(f"Error: Directory not found at {directory}")
        return []

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            html_files.append(os.path.join(directory, filename))
    print(f"Found {len(html_files)} HTML files in {directory}")
    return html_files

def parse_html_content(filepath: str) -> str:
    """Parses an HTML file and extracts main textual content."""
    print(f"Parsing: {os.path.basename(filepath)}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'lxml') # Use lxml parser

        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Basic content extraction (can be improved significantly)
        # Try to get text from common content tags, prioritizing 'article', then 'main', then 'body'
        main_content_tags = soup.find('article') or soup.find('main') or soup.body

        if main_content_tags:
            # Get text and clean up whitespace
            text = main_content_tags.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True) # Fallback to all text

        # Further cleanup (optional, can add more rules)
        lines = (line.strip() for line in text.splitlines()) # Split into lines
        chunks = (phrase.strip() for line in lines for phrase in line.split("  ")) # Split by multiple spaces
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk) # Join non-empty chunks with newline

        print(f" -> Extracted ~{len(cleaned_text)} characters.")
        return cleaned_text

    except FileNotFoundError:
        print(f"Error: File not found during parsing: {filepath}")
        return ""
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return ""

def save_parsed_content(parsed_data: dict, filename: str):
    """Saves the parsed content dictionary to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully saved parsed content to {filename}")
    except IOError as e:
        print(f"Error saving parsed content to {filename}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during save: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting Phase 3: HTML Content Parsing ---")

    html_files = list_html_files(HTML_DIR)
    # Store {original_url_source_filename: text_content}
    parsed_content = {}

    if not html_files:
        print("No HTML files found to parse. Exiting.")
    else:
        for filepath in html_files:
            filename = os.path.basename(filepath)
            content = parse_html_content(filepath)
            if content:
                # Store content using the filename (derived from URL) as the key
                parsed_content[filename] = content
            else:
                print(f" -> No content extracted.")

        if parsed_content:
            save_parsed_content(parsed_content, OUTPUT_FILE)
        else:
            print("No content was successfully parsed from any file.")

    # This block is now part of the run_parse function below
    # print("\nParsing finished.")
    # return len(parsed_content) > 0 # REMOVE THIS MISPLACED RETURN

def run_parse(input_html_dir: str = HTML_DIR, output_json_file: str = OUTPUT_FILE):
    """Parses HTML files from input dir and saves content to output JSON."""
    print(f"\n--- Running Parse Phase ---")
    print(f"Input Dir: {input_html_dir}, Output File: {output_json_file}")

    html_files = list_html_files(input_html_dir)
    parsed_content = {} # Dictionary to store {filename: text_content}

    if not html_files:
        print("No HTML files found to parse.")
        return False # Indicate failure or nothing to do
    else:
        for filepath in html_files:
            filename = os.path.basename(filepath)
            # Use the existing parse_html_content function
            content = parse_html_content(filepath)
            if content:
                parsed_content[filename] = content
            else:
                print(f" -> No content extracted from {filename}")

        if parsed_content:
            # Use the existing save_parsed_content function
            save_parsed_content(parsed_content, output_json_file)
            return True
        else:
            print("No content was successfully parsed from any file.")
            return False

# --- Main Execution (for standalone testing) ---
if __name__ == "__main__":
    print("--- Starting Standalone Parser Execution ---")
    # Use default config values for standalone run
    success = run_parse()
    if success:
        print("Standalone parsing completed successfully.")
    else:
        print("Standalone parsing completed, but no content was parsed or saved.")
    print("\n--- Standalone Parser Finished ---")
