import argparse
import json
import os
import traceback

def main():
    parser = argparse.ArgumentParser(description="Performs read, write, and delete operations on files.")
    parser.add_argument("--action", type=str, choices=["read", "write", "delete", "append"], required=True, help="Action to perform")
    parser.add_argument("--path", type=str, required=True, help="Path to the file")
    parser.add_argument("--content", type=str, default="", help="Content to write/append")
    args = parser.parse_args()

    try:
        result = {"status": "success", "action": args.action, "path": args.path}
        
        filepath = os.path.abspath(args.path)
        
        if args.action == "read":
            with open(filepath, 'r', encoding='utf-8') as f:
                result["content"] = f.read()
        elif args.action == "write":
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(args.content)
            result["message"] = "File written successfully."
        elif args.action == "append":
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(args.content)
            result["message"] = "Content appended successfully."
        elif args.action == "delete":
            if os.path.exists(filepath):
                os.remove(filepath)
                result["message"] = "File deleted successfully."
            else:
                result["status"] = "error"
                result["message"] = "File not found."

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
