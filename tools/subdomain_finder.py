import argparse
import json
import requests
import traceback

def get_subdomains(domain, max_results=100):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    subdomains = set()
    
    for entry in data:
        name_value = entry.get('name_value', '')
        # Handle multiple domains in one cert separated by newline
        for d in name_value.split('\n'):
            d = d.strip()
            if d.endswith(domain) and d != domain and not d.startswith('*'):
                subdomains.add(d)
                
    results = sorted(list(subdomains))
    if max_results and len(results) > max_results:
        results = results[:max_results]
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Finds subdomains for a given target domain using crt.sh certificate transparency logs.")
    parser.add_argument("--domain", type=str, required=True, help="Target domain (e.g., example.com)")
    parser.add_argument("--max_results", type=int, default=100, help="Maximum number of subdomains to return")
    args = parser.parse_args()

    try:
        subdomains = get_subdomains(args.domain, args.max_results)
        
        result = {
            "status": "success",
            "domain": args.domain,
            "count": len(subdomains),
            "subdomains": subdomains
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
