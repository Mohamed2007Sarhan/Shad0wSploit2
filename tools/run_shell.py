import argparse
import json
import subprocess
import traceback

def main():
    parser = argparse.ArgumentParser(description="Executes a terminal command safely and returns stdout/stderr.")
    parser.add_argument("--command", type=str, required=True, help="Shell command to execute")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    args = parser.parse_args()

    try:
        # We use shell=True since it's an AI agent tool running arbitrary commands
        process = subprocess.run(
            args.command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=args.timeout
        )
        
        result = {
            "status": "success" if process.returncode == 0 else "error_code",
            "command": args.command,
            "return_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
        print(json.dumps(result))
    except subprocess.TimeoutExpired:
        error_result = {
            "status": "error",
            "message": f"Command timed out after {args.timeout} seconds"
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
