"""
help_user.py — User Intelligence Injection Terminal
====================================================
Opens an interactive prompt where the human operator can type notes,
discoveries, or directives that will be injected as real-time intelligence
into the active AI agent session on the next agent turn.

Run this in a SEPARATE terminal window alongside main_agent.py.

Messages are written to:   tools/user_intel.json
The main agent reads them: each turn injects pending messages into context.

Usage (in a second terminal):
    python tools/help_user.py

Commands inside the prompt:
    <any text>   → queues the message for the AI
    /clear       → clear all pending messages
    /list        → list pending messages not yet consumed
    /quit        → exit this terminal
"""

import json
import os
import sys
import time
import threading

# ─── Colors (works on Win/Linux/Mac) ─────────────────────────────────────────
try:
    import colorama
    colorama.init(autoreset=True)
    C_CYAN   = "\033[96m"
    C_GREEN  = "\033[92m"
    C_YELLOW = "\033[93m"
    C_RED    = "\033[91m"
    C_BOLD   = "\033[1m"
    C_RESET  = "\033[0m"
except ImportError:
    C_CYAN = C_GREEN = C_YELLOW = C_RED = C_BOLD = C_RESET = ""

TOOLS_DIR  = os.path.dirname(os.path.abspath(__file__))
INTEL_FILE = os.path.join(TOOLS_DIR, "user_intel.json")

BANNER = f"""
{C_BOLD}{C_CYAN}
 +===========================================================+
 |       SHAD0WSPLOIT -- USER INTELLIGENCE TERMINAL         |
 |  Type your findings, tips, or directives below.          |
 |  The AI agent will read them on its next loop turn.      |
 +===========================================================+
{C_RESET}
 Commands:
   {C_YELLOW}<your message>{C_RESET}  -> send tip/intel to the AI
   {C_YELLOW}/clear{C_RESET}          -> clear all pending messages
   {C_YELLOW}/list{C_RESET}           -> show pending messages
   {C_YELLOW}/quit{C_RESET}           -> exit this terminal
"""


def _load():
    if os.path.exists(INTEL_FILE):
        try:
            with open(INTEL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"messages": []}


def _save(data):
    with open(INTEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def push_message(text: str):
    data = _load()
    data["messages"].append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "text": text.strip(),
        "consumed": False
    })
    _save(data)


def list_pending():
    data = _load()
    pending = [m for m in data["messages"] if not m.get("consumed")]
    return pending


def clear_messages():
    _save({"messages": []})


# ─── Status thread: shows pending count in title/line ─────────────────────────
def _status_updater():
    while True:
        pending = len(list_pending())
        sys.stdout.write(
            f"\r {C_CYAN}[Pending messages for AI: {C_YELLOW}{pending}{C_CYAN}]{C_RESET}  "
        )
        sys.stdout.flush()
        time.sleep(3)


def main():
    print(BANNER)

    # Start background status thread
    t = threading.Thread(target=_status_updater, daemon=True)
    t.start()

    while True:
        try:
            print()  # newline before prompt
            user_input = input(f" {C_GREEN}[USER INTEL]{C_RESET} › ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C_YELLOW}[!] Exiting User Intelligence Terminal.{C_RESET}")
            break

        if not user_input:
            continue

        if user_input.lower() == "/quit":
            print(f"{C_YELLOW}[!] Exiting.{C_RESET}")
            break

        elif user_input.lower() == "/clear":
            clear_messages()
            print(f"{C_GREEN}[✔] All pending messages cleared.{C_RESET}")

        elif user_input.lower() == "/list":
            pending = list_pending()
            if not pending:
                print(f"{C_YELLOW}  No pending messages.{C_RESET}")
            else:
                for i, m in enumerate(pending, 1):
                    print(f"  {C_CYAN}[{i}]{C_RESET} [{m['timestamp']}] {m['text']}")

        else:
            push_message(user_input)
            print(f"{C_GREEN}[✔] Message queued for AI agent:{C_RESET} \"{user_input}\"")


if __name__ == "__main__":
    main()
