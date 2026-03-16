import argparse
import json
import traceback
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(description="Compiles and runs a Go file and returns the output.")
    parser.add_argument("--file", type=str, required=True, help="Path to the .go file")
    parser.add_argument("--timeout", type=int, default=30, help="Execution timeout in seconds")
    args = parser.parse_args()

    try:
        filepath = os.path.abspath(args.file)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
            
        if not filepath.endswith('.go'):
            raise ValueError(f"File must be a .go file: {filepath}")

        # Try to run it using 'go run'
        cmd = f"go run {filepath}"
        
        process = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=args.timeout
        )
        
        result = {
            "status": "success" if process.returncode == 0 else "error_code",
            "file": args.file,
            "command": cmd,
            "return_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
        print(json.dumps(result))
        
    except subprocess.TimeoutExpired:
        error_result = {
            "status": "error",
            "message": f"Execution timed out after {args.timeout} seconds"
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
