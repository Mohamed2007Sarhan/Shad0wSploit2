import argparse
import json
import traceback
import requests

def main():
    parser = argparse.ArgumentParser(description="Makes HTTP GET/POST requests to APIs and returns JSON.")
    parser.add_argument("--method", type=str, choices=["GET", "POST", "PUT", "DELETE"], default="GET", help="HTTP method")
    parser.add_argument("--url", type=str, required=True, help="API URL to request")
    parser.add_argument("--headers", type=str, default="{}", help="JSON string of headers")
    parser.add_argument("--data", type=str, default=None, help="JSON string of data body for POST/PUT")
    args = parser.parse_args()

    try:
        headers = json.loads(args.headers)
        data = json.loads(args.data) if args.data else None
        
        response = requests.request(
            method=args.method,
            url=args.url,
            headers=headers,
            json=data if data else None,
            timeout=30
        )
        
        result = {
            "status": "success" if response.ok else "error_code",
            "status_code": response.status_code,
            "url": args.url,
            "headers_sent": headers
        }
        
        try:
            result["response_json"] = response.json()
        except ValueError:
            result["response_text"] = response.text
            
        print(json.dumps(result))
    except json.JSONDecodeError as e:
        error_result = {
            "status": "error",
            "message": f"Invalid JSON in headers or data: {str(e)}"
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
