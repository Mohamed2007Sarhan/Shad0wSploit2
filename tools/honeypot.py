import argparse
import json
import socket
import threading
import datetime
import traceback
import sys

def get_local_ips():
    ips = ['127.0.0.1', '::1', 'localhost']
    try:
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        ips.extend(local_ips)
    except Exception:
        pass
    return ips

def handle_connection(client_socket, address, log_file, whitelisted_ips):
    ip, port = address
    
    # CRITICAL REQUIREMENT: explicitly whitelist and ignore connections from localhost/own IP
    if ip in whitelisted_ips:
        client_socket.close()
        return

    timestamp = datetime.datetime.now().isoformat()
    try:
        data = client_socket.recv(1024)
        
        log_entry = {
            "timestamp": timestamp,
            "source_ip": ip,
            "source_port": port,
            "data_preview": repr(data[:100]) if data else "No data"
        }
        
        # Log to file
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
            
        # Optional: Send a fake response to keep them engaged
        fake_response = b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.1\r\n"
        client_socket.send(fake_response)
        
    except Exception:
        pass
    finally:
        client_socket.close()

def main():
    parser = argparse.ArgumentParser(description="A script to set up a basic honeypot listener on a specific port.")
    parser.add_argument("--port", type=int, required=True, help="Port to listen on")
    parser.add_argument("--log", type=str, default="honeypot.log", help="Log file path")
    parser.add_argument("--timeout", type=int, default=60, help="Stop listening after timeout (seconds). 0 for infinite.")
    args = parser.parse_args()

    try:
        whitelisted_ips = get_local_ips()
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', args.port))
        server.listen(5)
        server.settimeout(1.0) # 1 second timeout to check for overall timeout
        
        start_time = datetime.datetime.now()
        connections_handled = 0
        
        result = {
            "status": "started",
            "port": args.port,
            "log": args.log,
            "whitelisted_ips": whitelisted_ips,
            "message": f"Honeypot listening on port {args.port}"
        }
        print(json.dumps(result))
        sys.stdout.flush() # Ensure the agent gets the startup message
        
        while True:
            if args.timeout > 0:
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                if elapsed > args.timeout:
                    break
                    
            try:
                client, addr = server.accept()
                client.settimeout(5.0)
                connections_handled += 1
                
                # Handle in thread so we don't block
                client_handler = threading.Thread(
                    target=handle_connection,
                    args=(client, addr, args.log, whitelisted_ips)
                )
                client_handler.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                break
                
        server.close()
        
        if args.timeout > 0:
            completion = {
                "status": "completed",
                "connections_handled": connections_handled,
                "message": f"Honeypot stopped after {args.timeout} seconds timeout"
            }
            print(json.dumps(completion))
            
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
