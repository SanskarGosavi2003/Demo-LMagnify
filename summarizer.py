import google.generativeai as genai
# from google.generativeai import types # Not needed for this approach
import os
import json
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file
# Using the same key as Google Search, assuming it's enabled for Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PARSED_CONTENT_FILE = "parsed_content.json"
# Ensure this matches the query used in search_apis.py
ORIGINAL_QUERY = "latest advancements in AI fairness"
# Limit total characters of context sent to Gemini (adjust as needed)
MAX_CONTEXT_LENGTH = 30000
GEMINI_MODEL = "gemini-1.5-flash" # Using flash as it's generally faster/cheaper.
# GEMINI_MODEL = "gemini-1.5-pro-latest" # Or other models

# --- Functions ---

def load_parsed_content(filename: str) -> dict:
    """Loads parsed content from the JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = json.load(f)
        print(f"Loaded parsed content from {len(content)} files.")
        return content
    except FileNotFoundError:
        print(f"Error: Parsed content file not found at {filename}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred loading parsed content: {e}")
        return {}

def generate_response_stream(api_key: str, query: str, parsed_data: dict):
    """Generates a response using the Gemini API based on the query and parsed content, streaming the output."""
    if not api_key:
        print("Error: Google API Key not found in environment variables.")
        return

    try:
        # Configure the API key using the standard method
        genai.configure(api_key=api_key)
        # Initialize the model
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Combine parsed text snippets for context, respecting MAX_CONTEXT_LENGTH
        combined_context = ""
        context_sources = []
        for filename, text in parsed_data.items():
            source_info = f"\n\n--- Context from {filename} ---\n"
            if len(combined_context) + len(source_info) + len(text) < MAX_CONTEXT_LENGTH:
                combined_context += source_info + text
                context_sources.append(filename)
            else:
                remaining_len = MAX_CONTEXT_LENGTH - len(combined_context) - len(source_info)
                if remaining_len > 100: # Add partial content if space allows
                     combined_context += source_info + text[:remaining_len] + "..."
                     context_sources.append(f"{filename} (truncated)")
                print(f"\nWarning: Context truncated due to MAX_CONTEXT_LENGTH limit. Used sources: {', '.join(context_sources)}")
                break # Stop adding more context

        if not combined_context:
            print("Error: No parsed content available to use as context for Gemini.")
            return

        # Construct the prompt - asking to answer the query using the context
        prompt_text = f"""Please answer the following query, using the provided text snippets from web search results as context to inform your answer.

Original Query: "{query}"

--- Start of Provided Context ---
{combined_context}
--- End of Provided Context ---

Answer:"""

        print("\n--- Sending prompt to Gemini API & Streaming Response ---")
        # print(f"Prompt preview (first 500 chars):\n{prompt_text[:500]}...") # Uncomment for debugging

        # Use generate_content with stream=True
        response_stream = model.generate_content(prompt_text, stream=True)

        full_response = ""
        for chunk in response_stream:
            # Check for empty chunks or potential errors within chunks if needed
            if chunk.text:
                print(chunk.text, end="", flush=True) # Print immediately and flush buffer
                full_response += chunk.text

        # Check for blocking at the end of the stream
        # Accessing prompt_feedback might differ slightly with this method
        if not full_response:
             try:
                 # Check feedback after iteration (might be on the last chunk or the response object)
                 feedback = response_stream.prompt_feedback # Or potentially chunk.prompt_feedback if available on last chunk
                 if feedback and feedback.block_reason:
                     print(f"\nError: Gemini API call blocked. Reason: {feedback.block_reason}")
                 else:
                     print("\nError: Gemini API returned an empty response.")
             except Exception:
                 # Fallback if feedback attribute isn't readily available after streaming
                 print("\nError: Gemini API returned an empty response (unable to get feedback).")


    except Exception as e:
        # Catch potential API errors (authentication, network, etc.)
        print(f"\nError during Gemini API call: {e}")

def run_summarize(query: str, input_parsed_file: str = PARSED_CONTENT_FILE):
    """Loads parsed content and generates the Gemini response."""
    print(f"\n--- Running Summarize Phase for query: '{query}' ---")
    print(f"Input File: {input_parsed_file}")

    parsed_content_data = load_parsed_content(input_parsed_file)

    if not parsed_content_data:
        print("No parsed content loaded. Cannot generate summary.")
        # Decide if we should return an error indicator or just print
    else:
        # Use the existing generate_response_stream function
        generate_response_stream(GOOGLE_API_KEY, query, parsed_content_data)
        print() # Add a newline after streaming finishes

    print("\nSummarization finished.")
    # No explicit success/fail return needed as output is printed

# --- Main Execution (for standalone testing) ---
if __name__ == "__main__":
    print("--- Starting Standalone Summarizer Execution ---")
    # Use default config values and the hardcoded ORIGINAL_QUERY for standalone run
    run_summarize(ORIGINAL_QUERY, PARSED_CONTENT_FILE)
    print("\n--- Standalone Summarizer Finished ---")
