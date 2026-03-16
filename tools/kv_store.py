import argparse
import json
import os
import traceback

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_state(state_data):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state_data, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description="A local JSON-based Key-Value store to save and retrieve Agent state.")
    parser.add_argument("--action", type=str, choices=["set", "get", "delete", "list"], required=True, help="Action to perform")
    parser.add_argument("--key", type=str, help="Key for set/get/delete actions")
    parser.add_argument("--value", type=str, help="Value for set action (can be JSON string)")
    args = parser.parse_args()

    try:
        state = load_state()
        result = {"status": "success", "action": args.action}
        
        if args.action == "set":
            if not args.key or args.value is None:
                raise ValueError("Both --key and --value are required for 'set' action")
            
            # Try to parse value as JSON if possible, otherwise store as string
            try:
                parsed_value = json.loads(args.value)
            except json.JSONDecodeError:
                parsed_value = args.value
                
            state[args.key] = parsed_value
            save_state(state)
            result["key"] = args.key
            result["message"] = f"Key '{args.key}' set successfully"
            
        elif args.action == "get":
            if not args.key:
                raise ValueError("The --key argument is required for 'get' action")
            
            if args.key in state:
                result["key"] = args.key
                result["value"] = state[args.key]
            else:
                result["status"] = "not_found"
                result["message"] = f"Key '{args.key}' not found"
                
        elif args.action == "delete":
            if not args.key:
                raise ValueError("The --key argument is required for 'delete' action")
                
            if args.key in state:
                del state[args.key]
                save_state(state)
                result["key"] = args.key
                result["message"] = f"Key '{args.key}' deleted successfully"
            else:
                result["status"] = "not_found"
                result["message"] = f"Key '{args.key}' not found"
                
        elif args.action == "list":
            result["keys"] = list(state.keys())
            result["state"] = state
            
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
