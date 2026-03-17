import argparse
import json
import socket
import traceback
import concurrent.futures

def scan_port(ip, port, timeout):
    banner = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        if result == 0:
            # Try to grab a banner
            try:
                # Send a generic request to trigger a response from HTTP/similar protocols
                sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                data = sock.recv(1024)
                if data:
                    banner = data.decode('utf-8', errors='ignore').strip().split('\n')[0]
            except Exception:
                pass # Ignore timeout/errors during banner grabbing
            sock.close()
            return port, True, banner
        sock.close()
        return port, False, None
    except Exception:
        return port, False, None

def main():
    parser = argparse.ArgumentParser(description="Scans a specific port or a range of common ports on a target IP or hostname (DNS resolved).")
    parser.add_argument("--ip", type=str, required=True, help="Target IP address or hostname (DNS will be resolved automatically)")
    parser.add_argument("--ports", type=str, required=True, help="Comma-separated ports or 'common'")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout per port in seconds")
    parser.add_argument("--detailed", action="store_true", help="Enable detailed scanning/banner grabbing")
    args = parser.parse_args()

    try:
        # Resolve hostname or IP to a usable IP address
        # socket.gethostbyname works for both raw IPs and DNS names
        try:
            resolved_ip = socket.gethostbyname(args.ip)
        except socket.gaierror as dns_err:
            raise ValueError(f"Cannot resolve host '{args.ip}': {dns_err}")

        target_ports = []
        if args.ports.lower() == "common":
            target_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080]
        else:
            for p in args.ports.split(","):
                p_clean = p.strip()
                if "-" in p_clean:
                    start, end = p_clean.split("-")
                    if start.isdigit() and end.isdigit():
                        start_port = int(start)
                        end_port = int(end)
                        if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                            target_ports.extend(range(start_port, end_port + 1))
                        else:
                            raise ValueError(f"Invalid port range: {p}")
                    else:
                        raise ValueError(f"Invalid port range: {p}")
                elif p_clean.isdigit() and 1 <= int(p_clean) <= 65535:
                    target_ports.append(int(p_clean))
                else:
                    raise ValueError(f"Invalid port: {p}")

        open_ports_info = []
        closed_ports = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(scan_port, resolved_ip, port, args.timeout): port for port in target_ports}
            for future in concurrent.futures.as_completed(futures):
                port, is_open, banner = future.result()
                if is_open:
                    open_ports_info.append({"port": port, "banner": banner})
                else:
                    closed_ports.append(port)

        open_ports_info.sort(key=lambda x: x["port"])
        closed_ports.sort()

        result = {
            "status": "success",
            "target_input": args.ip,
            "resolved_ip": resolved_ip,
            "scanned_count": len(target_ports),
            "open_ports": open_ports_info,
            "closed_ports": closed_ports
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
