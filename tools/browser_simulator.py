import argparse
import json
import traceback
import time
import re

def main():
    parser = argparse.ArgumentParser(description="Uses Playwright to navigate to a URL, optionally scrolls, and extracts clean visible text.")
    parser.add_argument("--url", type=str, required=True, help="URL to navigate to")
    parser.add_argument("--scroll", action="store_true", help="Scroll down the page to trigger lazy-loaded elements")
    parser.add_argument("--timeout", type=int, default=30000, help="Navigation timeout in milliseconds")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError:
        error_result = {
            "status": "error",
            "message": "Playwright is not installed. Please run 'pip install playwright' and 'playwright install'."
        }
        print(json.dumps(error_result))
        return

    try:
        with sync_playwright() as p:
            # Launch headless chromium
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Navigate and wait for network idle to ensure dynamic content is loaded
            response = None
            try:
                response = page.goto(args.url, timeout=args.timeout, wait_until="networkidle")
            except PlaywrightTimeoutError:
                # If networkidle times out, the page might still be mostly loaded, so we catch and proceed
                pass
            
            # Ensure the body element is rendered
            page.wait_for_selector("body", timeout=10000)

            # Perform human-like scrolling if requested
            if args.scroll:
                last_height = page.evaluate("document.body.scrollHeight")
                # Scroll in increments to trigger lazy loading better than one big jump
                scroll_iterations = 0
                max_iterations = 20 # Prevent infinite scroll loops
                
                while scroll_iterations < max_iterations:
                    # Scroll down to bottom
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    # Give it time to load new content
                    time.sleep(1.5)
                    # Check new height
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break # Reached the bottom
                    last_height = new_height
                    scroll_iterations += 1

            # Extract visible text using Playwright's inner_text, which respects CSS visibility
            visible_text = page.locator("body").inner_text()
            
            # Clean up excessive newlines
            clean_text = re.sub(r'\n\s*\n', '\n\n', visible_text).strip()

            result = {
                "status": "success",
                "url": args.url,
                "title": page.title(),
                "text": clean_text
            }
            
            if response:
                result["status_code"] = response.status
                
            browser.close()
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
