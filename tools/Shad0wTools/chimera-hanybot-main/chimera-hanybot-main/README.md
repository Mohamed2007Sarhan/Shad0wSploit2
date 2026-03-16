# CHIMERA: Ultimate Surveillance & Active Defense System

![Chimera Defense](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.9-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-blue) ![License](https://img.shields.io/badge/License-MIT-orange)

**Chimera** is an advanced, deployment-ready deceptive defense system (Honeypot) designed to detect, monitor, and actively engage with network intruders. Unlike passive honeypots, Chimera functionality extends to **Active Defense**, employing counter-measures to identify and confuse attackers.

---

## ⚔️ Core Capabilities

### 👁️ The Hawk Eye (Packet Tracker)
*   **Real-time Sniffing:** continuously monitors network traffic for ICMP (Ping) and Nmap scans.
*   **Stealth Detection:** identifies scanning patterns and originating IP addresses instantly.
*   **Trigger Mechanism:** detection events immediately activate the "Hunter" module.

### 🏹 The Hunter (Active Defense Unit)
*   **Counter-Reconnaissance:** automatically launches a counter-scan against the attacker.
*   **OS Detection:** attempts to identify the attacker's operating system (e.g., checking Windows SMB ports).
*   **Redis Strike:** checks for open Redis instances on the attacker's machine and executes a "shutdown" command as a counter-measure.

### 🕸️ Virtual File System & Traps
*   **Fake SSH Environment:** A fully emulated shell implementation (`root@core:/root#`).
*   **Trap Files:**
    *   `critical_backup.tar` & `passwords.db`: Bait files designed to tempt attackers.
    *   **The Black Hole:** Attempting to exfiltrate trap files triggers an infinite stream of null bytes (simulating an 850 GB download), wasting the attacker's storage and bandwidth.
*   **Flag System:** standard CTF-style flags hidden within the virtual FS (`CTF{Scanning_Wont_Help_You}`).

### 🛡️ Secure Deployment
*   **Docker Isolation:** runs completely isolated within a Docker container.
*   **Network Firewalling:** `start.sh` automatically configures `iptables` to prevent the container from accessing your local LAN (192.168.x.x, 10.x.x.x), ensuring the honeypot cannot be used as a pivot point.

---

## 🔌 Trap Services

Chimera exposes the following high-value targets to lure attackers:

| Port (Host) | Port (Container) | Service | Description |
|:---:|:---:|:---:|:---|
| **22** | 2222 | **SSH** | Main trap interface with Virtual FS. |
| **80** | 8080 | **HTTP** | Web trap listener. |
| **21** | 2121 | **FTP** | Fake file server. |
| **9999** | 9999 | **VANITY** | "Show-off" port for extra logging. |

---

## 🚀 Installation & Usage

### Prerequisites
*   Linux Environment (or WSL2 on Windows)
*   Docker installed
*   Root privileges (for raw socket access and iptables management)

### Quick Start
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Mohamed2007Sarhan/chimera-hanybot.git
    cd chimera-hanybot
    ```

2.  **Deploy System:**
    Use the provided `start.sh` script to build the Docker image, run the container, and apply security rules.
    ```bash
    chmod +x start.sh
    sudo ./start.sh
    ```

    *The script will automatically stop old containers, build the new image `chimera-elite`, and map the necessary ports.*

3.  **Monitor Logs:**
    The system outputs colored logs to the console showing scans, hits, and active defense measures.
    
    ```
    [*] PACKET TRACKER ACTIVE: Sniffing for Pings & Scans...
    [!] HIT ON SSH (Trap) from 192.168.1.50
    [⚔️ HUNTER] Target: 192.168.1.50 | OS DETECTION: WINDOWS
    ```

---

## ⚠️ Disclaimer

**This tool is for EDUCATIONAL PURPOSES and AUTHORIZED DEFENSIVE TESTING only.** 
The "Active Defense" features (counter-scanning and service interaction) may be illegal in some jurisdictions if used against systems you do not own or have explicit permission to test. The author assumes no responsibility for misuse of this software.

---
*Created by Mohamed Sarhan*
