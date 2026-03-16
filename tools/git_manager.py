import argparse
import json
import traceback
import subprocess
import os

def run_git_command(repo_path, command, timeout=30):
    cmd = f"git {command}"
    process = subprocess.run(
        cmd,
        cwd=repo_path,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return {
        "command": cmd,
        "return_code": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip()
    }

def main():
    parser = argparse.ArgumentParser(description="Executes basic git commands (clone, commit, push).")
    parser.add_argument("--repo_path", type=str, required=True, help="Path to the git repository")
    parser.add_argument("--action", type=str, choices=["init", "clone", "status", "add", "commit", "push", "pull"], required=True, help="Git action to perform")
    parser.add_argument("--url", type=str, help="Repository URL for clone action")
    parser.add_argument("--message", type=str, help="Commit message for commit action")
    parser.add_argument("--files", type=str, default=".", help="Files to add for add action (default: '.')")
    parser.add_argument("--branch", type=str, default="main", help="Branch name for push/pull actions")
    args = parser.parse_args()

    try:
        repo_path = os.path.abspath(args.repo_path)
        result = {
            "status": "success",
            "action": args.action,
            "repo_path": repo_path
        }
        
        if args.action == "clone":
            if not args.url:
                raise ValueError("The --url argument is required for 'clone' action")
            # Clone doesn't need to run inside the repo directory (since it doesn't exist yet)
            parent_dir = os.path.dirname(repo_path)
            os.makedirs(parent_dir, exist_ok=True)
            cmd = f"git clone {args.url} {repo_path}"
            
            process = subprocess.run(cmd, cwd=parent_dir, shell=True, capture_output=True, text=True, timeout=120)
            
            result["return_code"] = process.returncode
            result["stdout"] = process.stdout.strip()
            result["stderr"] = process.stderr.strip()
            if process.returncode != 0:
                result["status"] = "error_code"
                
        else:
            # All other commands must be run inside the repository
            if args.action == "init":
                os.makedirs(repo_path, exist_ok=True)
                cmd_res = run_git_command(repo_path, "init")
                
            elif args.action == "status":
                cmd_res = run_git_command(repo_path, "status")
                
            elif args.action == "add":
                cmd_res = run_git_command(repo_path, f"add {args.files}")
                
            elif args.action == "commit":
                if not args.message:
                    raise ValueError("The --message argument is required for 'commit' action")
                # Quote the message carefully
                safe_msg = args.message.replace('"', '\\"')
                cmd_res = run_git_command(repo_path, f'commit -m "{safe_msg}"')
                
            elif args.action == "push":
                cmd_res = run_git_command(repo_path, f"push origin {args.branch}")
                
            elif args.action == "pull":
                cmd_res = run_git_command(repo_path, f"pull origin {args.branch}")

            result.update(cmd_res)
            if result.get("return_code", 0) != 0:
                result["status"] = "error_code"

        print(json.dumps(result))
    except subprocess.TimeoutExpired:
        error_result = {
            "status": "error",
            "message": "Git command timed out"
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
