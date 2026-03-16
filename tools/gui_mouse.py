import argparse
import pyautogui
import time
import json
import traceback

def main():
    parser = argparse.ArgumentParser(description="GUI Mouse & Keyboard Controller")
    parser.add_argument("--action", required=True, choices=["click", "double_click", "right_click", "move", "type", "press"], help="Action to perform")
    parser.add_argument("--x", type=int, help="X coordinate for mouse actions")
    parser.add_argument("--y", type=int, help="Y coordinate for mouse actions")
    parser.add_argument("--text", type=str, help="Text to type for 'type' action")
    parser.add_argument("--key", type=str, help="Key to press for 'press' action (e.g., 'enter', 'tab', 'win')")
    parser.add_argument("--wait", type=float, default=0.5, help="Wait time after action in seconds")

    args = parser.parse_args()
    
    try:
        action_str = "None"
        if args.action in ["click", "double_click", "right_click", "move"]:
            if args.x is None or args.y is None:
                print(json.dumps({"status": "error", "message": "--x and --y are required for mouse actions."}))
                return
                
            # Safely move mouse to coordinates
            pyautogui.moveTo(args.x, args.y, duration=0.2)
            
            if args.action == "click":
                pyautogui.click(args.x, args.y)
                action_str = f"Clicked at ({args.x}, {args.y})"
            elif args.action == "double_click":
                pyautogui.doubleClick(args.x, args.y)
                action_str = f"Double-clicked at ({args.x}, {args.y})"
            elif args.action == "right_click":
                pyautogui.rightClick(args.x, args.y)
                action_str = f"Right-clicked at ({args.x}, {args.y})"
            elif args.action == "move":
                action_str = f"Moved mouse to ({args.x}, {args.y})"
                
        elif args.action == "type":
            if not args.text:
                print(json.dumps({"status": "error", "message": "--text is required for type action."}))
                return
            # Typing with small interval to simulate real typing
            pyautogui.typewrite(args.text, interval=0.05)
            action_str = f"Typed text: '{args.text}'"
            
        elif args.action == "press":
            if not args.key:
                print(json.dumps({"status": "error", "message": "--key is required for press action."}))
                return
            pyautogui.press(args.key)
            action_str = f"Pressed key: '{args.key}'"
            
        time.sleep(args.wait)
        result = {
            "status": "success",
            "action": action_str
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
