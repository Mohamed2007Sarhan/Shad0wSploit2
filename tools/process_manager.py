import argparse
import json
import traceback
import psutil

def main():
    parser = argparse.ArgumentParser(description="Lists running processes or kills a process by PID.")
    parser.add_argument("--action", type=str, choices=["list", "kill", "find"], required=True, help="Action to perform")
    parser.add_argument("--pid", type=int, help="Process ID to kill or find")
    parser.add_argument("--name", type=str, help="Process name to find")
    args = parser.parse_args()

    try:
        result = {"status": "success", "action": args.action}

        if args.action == "list":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            result["processes"] = processes
            
        elif args.action == "kill":
            if not args.pid:
                raise ValueError("The --pid argument is required for 'kill' action")
            proc = psutil.Process(args.pid)
            proc.terminate()
            proc.wait(timeout=3)
            result["message"] = f"Process {args.pid} terminated"
            
        elif args.action == "find":
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (args.pid and proc.info['pid'] == args.pid) or \
                       (args.name and args.name.lower() in proc.info['name'].lower()):
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            result["processes"] = processes

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
