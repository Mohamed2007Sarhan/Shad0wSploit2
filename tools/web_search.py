import argparse
import json
import traceback
from ddgs import DDGS

def main():
    parser = argparse.ArgumentParser(description="Performs a web search using the official ddgs library.")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--max_results", type=int, default=5, help="Maximum number of results to return")
    args = parser.parse_args()

    try:
        results = []
        # Use DDGS context manager for proper connection handling
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(args.query, max_results=args.max_results))
            
            for item in raw_results:
                # Map DDGS keys ('title', 'href', 'body') to our standard ('title', 'url', 'snippet')
                results.append({
                    "title": item.get('title', ''),
                    "url": item.get('href', ''),
                    "snippet": item.get('body', '')
                })
        
        result = {
            "status": "success",
            "query": args.query,
            "results": results
        }
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
