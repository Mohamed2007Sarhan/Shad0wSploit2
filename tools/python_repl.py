import argparse
import json
import traceback
import sys
import io

def main():
    parser = argparse.ArgumentParser(description="Executes Python code in an isolated environment.")
    parser.add_argument("--code", type=str, required=True, help="Python code to execute")
    args = parser.parse_args()

    try:
        # Redirect stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = sys.stdout = io.StringIO()
        redirected_error = sys.stderr = io.StringIO()

        # Create a clean environment dictionary
        env = {}
        
        # Execute the code
        try:
            exec(args.code, env)
            exec_error = None
        except Exception as e:
            exec_error = str(e)
            traceback.print_exc()

        # Restore stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        stdout_val = redirected_output.getvalue()
        stderr_val = redirected_error.getvalue()

        result = {
            "status": "success" if not exec_error else "error_code",
            "code": args.code,
            "stdout": stdout_val,
            "stderr": stderr_val
        }
        
        if exec_error:
            result["execution_error"] = exec_error
            
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))
    finally:
        # Just in case of unhandled exception during exec
        if 'old_stdout' in locals():
            sys.stdout = old_stdout
        if 'old_stderr' in locals():
            sys.stderr = old_stderr

if __name__ == "__main__":
    main()
