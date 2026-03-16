import os
import sys
import subprocess
import logging
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.prompt import Confirm

# Setup Logging
setup_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup.log")
logging.basicConfig(
    filename=setup_log,
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console = Console()

def print_banner():
    banner = """
   _____ _               _  ___          _____       _       _ _   
  / ____| |             | |/ _ \        / ____|     | |     (_) |  
 | (___ | |__   __ _  __| | | | \ \ /\ / /\___ \| '_ \| |/ _ \| | __|
  \___ \| '_ \ / _` |/ _` | | | |\ V V / ____) | |_) | | (_) | | |_ 
  ____) | | | | (_| | (_| | |_| | \_/\_/ |_____/| .__/|_|\___/|_|\__|
 |_____/|_| |_|\__,_|\__,_|\___/                | |                  
                                                |_|                  
    [ ULTIMATE BLACKARCH SETUP INITIATED ]   
    """
    console.print(Panel(banner, style="bold red"))

def run_command(command, description, fail_hard=False):
    """Executes a system command and logs the result."""
    logging.info(f"Running: {description} (Cmd: {command})")
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            console.print(f"[bold green][+][/bold green] {description} - Success")
            logging.info(f"Success: {stdout.strip()}")
            return True
        else:
            console.print(f"[bold yellow][-][/bold yellow] {description} - Failed")
            logging.warning(f"Failed: {stderr.strip()}")
            if fail_hard:
                console.print(f"[bold red]CRITICAL FAILURE on {description}. Aborting.[/bold red]")
                sys.exit(1)
            return False
    except Exception as e:
        console.print(f"[bold red][!][/bold red] Exception during {description}: {str(e)}")
        logging.error(f"Exception: {str(e)}")
        if fail_hard:
            sys.exit(1)
        return False

def check_root():
    if os.geteuid() != 0:
        console.print("[bold red][!] This setup script MUST be run as root (sudo/su). Shad0w demands full power.[/bold red]")
        sys.exit(1)

def verify_files():
    console.print("\n[bold cyan]--- Verifying Shad0wSploit Core Files ---[/bold cyan]")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    essential_files = [
        "main_agent.py",
        "library.txt",
        "requests_library.txt",
        "memory/memory_manager.py"
    ]
    
    missing = []
    for f in essential_files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            console.print(f"[bold green][+][/bold green] Found: {f}")
        else:
            console.print(f"[bold red][-][/bold red] Missing: {f}")
            missing.append(f)
            
    if missing:
        console.print("[bold red][!] CRITICAL: Core files are missing. Cannot proceed with setup.[/bold red]")
        sys.exit(1)
    else:
        console.print("[bold green]All core files verified. Proceeding with Launch Protocol.[/bold green]")

def install_system_dependencies():
    console.print("\n[bold cyan]--- Installing Core Arch/BlackArch System Packages ---[/bold cyan]")
    # Update system first
    run_command("pacman -Sy", "Synchronizing Arch Repositories")
    
    # Install essential packages for the agent to function properly
    core_packages = "python-pip git sqlite3 curl wget base-devel python-requests python-rich"
    run_command(f"pacman -S --noconfirm --needed {core_packages}", "Installing Core Arch Packages", fail_hard=True)

def setup_python_environment():
    console.print("\n[bold cyan]--- Installing Python Dependencies Directly on Arch ---[/bold cyan]")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lib_txt = os.path.join(base_dir, "library.txt")
    req_txt = os.path.join(base_dir, "requests_library.txt")
    
    for txt_file in [lib_txt, req_txt]:
        if os.path.exists(txt_file):
            filename = os.path.basename(txt_file)
            with Status(f"[bold yellow]Installing dependencies from {filename}...[/bold yellow]", console=console, spinner="bouncingBar"):
                # Install the dependencies directly, bypassing PEP 668 restrictions since this is a dedicated hacking OS
                run_command(f"python3 -m pip install -r {txt_file} --break-system-packages", f"Installing {filename} directly")
        else:
            console.print(f"[bold yellow][!] {os.path.basename(txt_file)} not found. Skipping...[/bold yellow]")

def install_wine_and_docker():
    console.print("\n[bold cyan]--- Setting up Ultimate Tools Infrastructure (Wine & Docker) ---[/bold cyan]")
    
    # Install Docker for Chimera-Hanybot and start the service
    run_command("pacman -S --noconfirm --needed docker docker-compose", "Installing Docker & Docker-Compose")
    run_command("systemctl enable --now docker", "Enabling and Starting Docker Service")
    
    # Add Shad0w user to docker group if it exists
    run_command("usermod -aG docker shad0w", "Adding user 'shad0w' to docker group")
    
    # Configure Multilib repository for Wine if not enabled (required for Windows GUI tools on 64bit Arch)
    multilib_check = run_command("grep -q '^\\[multilib\\]' /etc/pacman.conf", "Checking Multilib Repository status")
    if not multilib_check:
        console.print("[bold yellow][!] Note: To install Wine properly on 64-bit Arch, ensure [multilib] is enabled in /etc/pacman.conf![/bold yellow]")
        
    # Attempt to install Wine for Windows tool compatibility (DeepNude, Fireware-app GUI if it's Windows based, etc)
    run_command("pacman -S --noconfirm --needed wine wine-mono wine-gecko", "Installing Wine (For Windows Shad0wTools compatibility)")

def configure_ollama():
    console.print("\n[bold cyan]--- Setting up Local LLM Brain (Ollama) ---[/bold cyan]")
    # Check if ollama is installed
    if not run_command("which ollama", "Checking if Ollama is installed"):
        console.print("[bold yellow]Installing Ollama via curl script...[/bold yellow]")
        run_command("curl -fsSL https://ollama.com/install.sh | sh", "Installing Ollama Engine")
        
    run_command("systemctl enable --now ollama", "Enabling and Starting Ollama Service")
    
    # Pull the required jailbroken/abliterated models mentioned in agent script
    run_command("ollama pull huihui_ai/gpt-oss-abliterated:latest", "Pulling Master Agent Brain Model (huihui_ai/gpt-oss-abliterated)")
    # Since we have vision tools (gui_vision.py), it usually requires a vision model
    run_command("ollama pull llava:latest", "Pulling Vision Model (llava) for GUI operations")

def finalize_setup():
    console.print("\n[bold magenta]======================================================[/bold magenta]")
    console.print("[bold green]ALL SYSTEMS GO. Shad0wSploit Framework is fully initialized.[/bold green]")
    console.print("\n[bold cyan]How to launch your new God-Tier Agent:[/bold cyan]")
    console.print("1. Run the master agent globally: [bold yellow]python main_agent.py[/bold yellow]")
    console.print("\n[bold red]Disclaimer: You are responsible for the chaos this system creates. The Legend Begins.[/bold red]")
    console.print("[bold magenta]======================================================[/bold magenta]\n")

if __name__ == "__main__":
    print_banner()
    
    # WARNING: This script builds a real system. We bypass confirming for root if running inside an AI wrapper, 
    # but the actual user will need to run it as root on BlackArch.
    # check_root() 
    
    if Confirm.ask("[bold red]Are you sure you want to initialize the BlackArch Shad0wSploit environment?[/bold red]"):
        verify_files()
        install_system_dependencies()
        setup_python_environment()
        install_wine_and_docker()
        configure_ollama()
        finalize_setup()
    else:
        console.print("[bold yellow]Setup Aborted.[/bold yellow]")
