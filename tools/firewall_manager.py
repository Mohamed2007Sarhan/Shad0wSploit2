import argparse
import json
import subprocess
import traceback
import platform

def run_cmd(cmd):
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if process.returncode != 0:
        if "Access is denied" in process.stderr or "Permission denied" in process.stderr or "requires elevation" in process.stderr or "requires elevation" in process.stdout or "run as administrator" in process.stdout.lower():
            raise PermissionError(f"Command failed due to permissions: {process.stderr or process.stdout}")
        raise RuntimeError(f"Command failed: {process.stderr or process.stdout}")
    return process.stdout

def block_ip_windows(ip):
    rule_name = f"Block_{ip}"
    cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip}'
    return run_cmd(cmd)

def unblock_ip_windows(ip):
    rule_name = f"Block_{ip}"
    cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
    return run_cmd(cmd)

def block_ip_linux(ip):
    cmd = f'iptables -A INPUT -s {ip} -j DROP'
    return run_cmd(cmd)

def unblock_ip_linux(ip):
    cmd = f'iptables -D INPUT -s {ip} -j DROP'
    return run_cmd(cmd)

def main():
    parser = argparse.ArgumentParser(description="A script to simulate adding/removing firewall rules.")
    parser.add_argument("--action", type=str, choices=["block", "unblock"], required=True, help="Action to perform")
    parser.add_argument("--ip", type=str, required=True, help="Target IP address")
    args = parser.parse_args()

    try:
        os_name = platform.system().lower()
        output = ""
        
        if os_name == "windows":
            if args.action == "block":
                output = block_ip_windows(args.ip)
            else:
                output = unblock_ip_windows(args.ip)
        elif os_name == "linux":
            if args.action == "block":
                output = block_ip_linux(args.ip)
            else:
                output = unblock_ip_linux(args.ip)
        else:
            raise NotImplementedError(f"Unsupported OS: {os_name}")

        result = {
            "status": "success",
            "action": args.action,
            "ip": args.ip,
            "os": os_name,
            "output": output.strip()
        }
        print(json.dumps(result))
        
    except PermissionError as e:
        error_result = {
            "status": "error",
            "error_type": "PermissionError",
            "message": str(e),
            "suggestion": "Run the Agent or this script with Administrator/root privileges."
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
