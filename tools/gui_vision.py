import argparse
import pyautogui
import base64
import requests
from io import BytesIO
import time
import json
import os
import traceback

def take_screenshot_as_base64():
    """Takes a screenshot of the desktop and converts it to base64."""
    screenshot = pyautogui.screenshot()
    buffered = BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    width, height = screenshot.size
    return img_str, width, height

def ask_vision_model(prompt_text, image_base64):
    """Sends the base64 image and prompt to Ollama."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gpt-oss", # Vision model configured in user's Ollama
        "prompt": prompt_text,
        "images": [image_base64],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Request Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="GUI Vision Tool for taking a screenshot and analyzing it via Ollama.")
    parser.add_argument("--prompt", required=True, help="Instruction for the vision AI (e.g. 'find the login button coordinates in JSON format')")
    parser.add_argument("--app", required=False, help="Optional application command to launch before taking a screenshot")
    parser.add_argument("--wait", type=int, default=2, help="Seconds to wait before taking the screenshot so the app can load")
    args = parser.parse_args()
    
    try:
        if args.app:
            try:
                # Simple subprocess open, tailored for Windows (using start command)
                os.system(f"start \"\" {args.app}")
            except Exception as e:
                pass
                
        if args.wait > 0:
            time.sleep(args.wait)
            
        screen_base64, width, height = take_screenshot_as_base64()
        
        analysis = ask_vision_model(args.prompt, screen_base64)
        
        result = {
            "status": "success",
            "screen_resolution": {"width": width, "height": height},
            "vision_analysis": analysis
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
