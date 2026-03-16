import socket
import time

NGROK_HOST = "4.tcp.eu.ngrok.io"
NGROK_PORT = 12035
INTERVAL_SECONDS = 90

def keep_alive():
    print(f"--- Monitoring Ngrok Tunnel: {NGROK_HOST}:{NGROK_PORT} ---")
    print(f"--- Frequency: Every {INTERVAL_SECONDS} seconds ---")
    
    while True:
        try:
            with socket.create_connection((NGROK_HOST, NGROK_PORT), timeout=10):
                current_time = time.strftime('%H:%M:%S')
                print(f"[{current_time}] Connection successful: Pulse sent.")
        except Exception as e:
            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] Warning: Connection failed! (Reason: {e})")
        
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        keep_alive()
    except KeyboardInterrupt:
        print("\n[!] Script stopped by user.")