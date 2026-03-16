import argparse
import json
import traceback
import requests
from bs4 import BeautifulSoup
import re

def main():
    parser = argparse.ArgumentParser(description="Scrapes and extracts clean, readable text from a given URL.")
    parser.add_argument("--url", type=str, required=True, help="URL to fetch")
    args = parser.parse_args()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(args.url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            script.decompose()
            
        # Extract text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        result = {
            "status": "success",
            "url": args.url,
            "title": soup.title.string.strip() if soup.title and soup.title.string else "",
            "text": clean_text[:10000] # Limit to 10k chars to avoid huge outputs
        }
        print(json.dumps(result))
    except requests.exceptions.RequestException as e:
        error_result = {
            "status": "error",
            "message": f"Failed to fetch URL: {str(e)}"
        }
        print(json.dumps(error_result))
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
