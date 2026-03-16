<div align="center">

# 💀 SHAD0WSPLOIT 💀

*Autonomous AI Agent Framework / ReAct Engine*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)]()
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge&logo=ollama&logoColor=white)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)]()

*“The shadow that thinks, plans, and executes.”*

</div>

---

## ⚡ What is Shad0wSploit?

**Shad0wSploit** is a ruthless, highly autonomous AI Agent Framework designed for complex, multi-step execution. Powered by local LLMs (Ollama) and built on a strict **ReAct (Reasoning & Action)** loop, this engine does not just talk—it *does*.

Unlike static chatbots, Shad0wSploit operates organically:
1. **It Thinks:** Evaluates the target and its current progress.
2. **It Acts:** Dynamically invokes standalone Python tools from its arsenal.
3. **It Learns:** Analyzes the exact terminal output (success or failure) and self-corrects on the fly.

Give it a target, sit back, and watch the terminal light up as it hacks its way to a solution.

---

## 🔥 Core Features

- 🧠 **Relentless Execution Loop**: Parses your objective, breaks it down, and executes tools step-by-step. It refuses to quit until the `FINISH` action is achieved.
- 🛡️ **Self-Healing & Error Correction**: If a tool fails or throws an exception, Shad0wSploit reads the stderr, understands its mistake, and rewrites its approach.
- 💾 **Persistent SQLite Memory**: Never loses its train of thought. Every task has an isolated workspace maintaining its history, plans, and deductions (`memory_manager.py`).
- 🛠️ **Plug-and-Play Tool Arsenal**: Dynamic tool discovery. Drop any Python script using `argparse` into the `tools/` directory, and Shad0wSploit will automatically read its `--help` signature and learn how to wield it. Zero hardcoding required.
- 🎨 **Cinematic CLI Interface**: Built with the `rich` library. Color-coded thoughts (Purple), actions (Yellow), and outputs (Green) make tracking the AI's internal monologue a visually stunning experience.

---

## 📂 Architecture

```text
Shad0wSploit/
│
├── main_agent.py          # The Core Orchestrator & ReAct Engine
├── setup.py               # Package installer configurations
├── requirements.txt       # Python dependencies
│
├── memory/
│   ├── memory_manager.py  # SQLite Database & State Control
│   └── master_tasks.db    # (Generated) Global task history tracker
│
└── tools/                 # The Arsenal (Drop new tools here)
    ├── system_shell.py    # Example: Executes bash/cmd commands
    ├── web_scraper.py     # Example: Scrapes HTML targets
    └── ...
```

---

## 🚀 Installation

Ensure you have [Python 3.9+](https://www.python.org/downloads/) and [Ollama](https://ollama.com/) installed locally.

**1. Clone the Repository:**
```bash
git clone https://github.com/yourusername/shad0wsploit.git
cd shad0wsploit
```

**2. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**3. Start the Local AI Engine:**
*(By default, Shad0wSploit targets `huihui_ai/gpt-oss-abliterated:latest`. Ensure this model is pulled, or change the target in `main_agent.py`)*
```bash
ollama run huihui_ai/gpt-oss-abliterated:latest
```

---

## 💻 Usage

Launch the main CLI orchestrator:

```bash
python main_agent.py
```

You will be greeted by the Shad0wSploit Neural Interface:
1. Select **[1] Start New Task**.
2. Give the task a codename.
3. Provide the Ultimate Objective (e.g., *"Write a Python script to port scan my local network and save the results in a file."*).

Watch the terminal as the Agent thinks, acts, and iterates until the objective is crushed. 

When it finishes, it will ask for your next directive to keep the session alive indefinitely.

---

## 🛠️ Expanding the Arsenal

To make Shad0wSploit smarter, just give it more tools!

Create a standalone Python script in the `tools/` directory. Use `argparse` to define the arguments. Shad0wSploit will automatically parse the help text and integrate it into its capabilities on the next boot.

*Example Tool (`tools/ping_sweep.py`):*
```python
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pings a target to check if it's alive.")
    parser.add_argument("--target", required=True, help="The IP or Domain to ping.")
    args = parser.parse_args()
    
    # Tool logic here...
    os.system(f"ping -c 4 {args.target}")
```

---

## ⚠️ Disclaimer

Shad0wSploit is an autonomous agent capable of executing terminal commands directly on your machine. **It is highly recommended to run this framework inside an isolated Virtual Machine (VM) or Docker Container.** 

The authors are not responsible for any damage, deleted files, or system compromises resulting from the autonomous execution of commands. **Use at your own risk.**
