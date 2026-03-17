"""
run_shell_adv.py — Advanced Persistent Shell Session Manager
=============================================================
Cross-platform persistent shell that keeps ONE shell process alive across
multiple commands. State (env vars, cwd, tool sessions like msfconsole)
is preserved between calls.

Platform auto-detection:
  Windows → cmd.exe /v:on /k
  Linux   → /bin/bash
  macOS   → /bin/bash (or zsh)

Features:
  ✔ Persistent state across calls (env vars, cd, msfconsole sessions, etc.)
  ✔ Visible terminal window mode (--show-window) so you can watch live
  ✔ SQLite session DB (tools/shell_adv.db)
  ✔ Cross-platform: Windows, Linux (BlackArch/Kali), macOS
  ✔ No hardcoded timeouts — commands run as long as they need

Architecture:
  - A background Python SERVER is spawned once per session.
  - The server holds the real shell subprocess (stdin/stdout piped).
  - The client sends commands via request.json, reads via response.json.
  - In --show-window mode, a visible terminal window is ALSO opened that
    mirrors session output (via a tail of the session log file).

Usage:
  run_shell_adv.py --new-session [--show-window]
  run_shell_adv.py --session-id <id> --command "msfconsole"
  run_shell_adv.py --session-id <id> --command "use exploit/..."
  run_shell_adv.py --list-sessions
  run_shell_adv.py --session-id <id> --kill-session
"""

import argparse
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import uuid

# ─── Constants ────────────────────────────────────────────────────────────────

TOOLS_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(TOOLS_DIR, "shell_adv.db")
SENTINEL    = "<<<SHAD0W_DONE_7F3A>>>"
SERVER_FLAG = "--_srv_"   # internal: server mode marker

OS_NAME = platform.system()  # 'Windows', 'Linux', 'Darwin'


def _get_shell():
    """Return the best shell command for this OS."""
    if OS_NAME == "Windows":
        return ["cmd.exe", "/v:on", "/k"]
    else:
        # Linux (BlackArch, Kali, etc.) and macOS
        for sh in ["/bin/bash", "/bin/zsh", "/bin/sh"]:
            if os.path.exists(sh):
                return [sh, "--norc", "--noprofile"]
        return ["/bin/sh"]


def _sentinel_cmd():
    """Echo the sentinel string — platform-aware."""
    if OS_NAME == "Windows":
        return f"echo {SENTINEL}\r\n"
    else:
        return f"echo '{SENTINEL}'\n"


# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            last_used  TEXT NOT NULL,
            status     TEXT NOT NULL DEFAULT 'active',
            pid        INTEGER,
            sess_dir   TEXT,
            platform   TEXT
        );
        CREATE TABLE IF NOT EXISTS command_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp  TEXT NOT NULL,
            command    TEXT NOT NULL,
            output     TEXT,
            rc         INTEGER
        );
    """)
    conn.commit()
    conn.close()


# ─── Session paths ────────────────────────────────────────────────────────────

def _sdir(sid):
    d = os.path.join(tempfile.gettempdir(), f"shad0w_adv_{sid}")
    os.makedirs(d, exist_ok=True)
    return d

def _req(sid):   return os.path.join(_sdir(sid), "request.json")
def _resp(sid):  return os.path.join(_sdir(sid), "response.json")
def _alive(sid): return os.path.join(_sdir(sid), "alive.flag")
def _kill(sid):  return os.path.join(_sdir(sid), "kill.flag")
def _log(sid):   return os.path.join(_sdir(sid), "session.log")


# ─── SERVER ───────────────────────────────────────────────────────────────────

def _run_server(sid):
    """Long-running server process: one shell alive, routes commands via files."""
    rq    = _req(sid)
    rp    = _resp(sid)
    alive = _alive(sid)
    kf    = _kill(sid)
    logf  = _log(sid)

    with open(alive, "w") as f:
        f.write(str(os.getpid()))

    shell_cmd = _get_shell()

    creation_flags = 0
    if OS_NAME == "Windows":
        creation_flags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        shell_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creation_flags
    )

    def write_log(text):
        try:
            with open(logf, "a", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

    def send_and_read(command):
        if OS_NAME == "Windows":
            full = f"{command}\r\necho {SENTINEL}\r\n"
        else:
            full = f"{command}\necho '{SENTINEL}'\n"

        try:
            proc.stdin.write(full)
            proc.stdin.flush()
        except Exception as e:
            return f"[SHELL WRITE ERROR] {e}", -1

        lines = []
        while True:
            try:
                line = proc.stdout.readline()
            except Exception:
                break
            if not line:
                break
            stripped = line.rstrip()
            if SENTINEL in stripped:
                break
            lines.append(stripped)
            write_log(stripped + "\n")

        return "\n".join(lines).strip(), 0

    # Drain startup banner
    if OS_NAME == "Windows":
        drain = f"echo {SENTINEL}\r\n"
    else:
        drain = f"echo '{SENTINEL}'\n"
    try:
        proc.stdin.write(drain)
        proc.stdin.flush()
        while True:
            line = proc.stdout.readline()
            if not line or SENTINEL in line:
                break
    except Exception:
        pass

    write_log(f"=== Session {sid} started [{OS_NAME}] ===\n")

    # Main loop
    while True:
        if os.path.exists(kf):
            break

        if not os.path.exists(rq):
            time.sleep(0.15)
            continue

        try:
            with open(rq, "r", encoding="utf-8") as f:
                req_data = json.load(f)
            os.remove(rq)
        except Exception:
            time.sleep(0.1)
            continue

        command = req_data.get("command", "")
        write_log(f"\n>>> {command}\n")

        output, _ = send_and_read(command)

        # Get exit code
        if OS_NAME == "Windows":
            rc_out, _ = send_and_read("echo __RC__%ERRORLEVEL%__RC__")
        else:
            rc_out, _ = send_and_read("echo __RC__$?__RC__")

        rc = 0
        if "__RC__" in rc_out:
            try:
                rc = int(rc_out.split("__RC__")[1].strip())
            except Exception:
                rc = 0

        resp = {"output": output, "rc": rc}
        try:
            with open(rp, "w", encoding="utf-8") as f:
                json.dump(resp, f, ensure_ascii=False)
        except Exception:
            pass

        # DB log
        try:
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            conn = get_db()
            conn.execute(
                "INSERT INTO command_log(session_id,timestamp,command,output,rc) VALUES(?,?,?,?,?)",
                (sid, now, command, output, rc)
            )
            conn.execute("UPDATE sessions SET last_used=? WHERE session_id=?", (now, sid))
            conn.commit()
            conn.close()
        except Exception:
            pass

    # Shutdown shell
    try:
        if OS_NAME == "Windows":
            proc.stdin.write("exit\r\n")
        else:
            proc.stdin.write("exit\n")
        proc.stdin.flush()
        proc.wait(timeout=3)
    except Exception:
        proc.kill()

    if os.path.exists(alive):
        os.remove(alive)


# ─── Visible window launcher ──────────────────────────────────────────────────

def _launch_visible_window(sid):
    """
    Opens a VISIBLE terminal window that tails the session log file so the
    user can watch commands/output in real time on any OS.
    """
    logf = _log(sid)
    title = f"Shad0wSploit Live Shell — Session {sid}"

    if OS_NAME == "Windows":
        # Windows Terminal or fallback to cmd
        tail_script = os.path.join(_sdir(sid), "tail_log.py")
        with open(tail_script, "w") as f:
            f.write(f"""
import time, os, sys
path = r"{logf}"
title = "{title}"
os.system(f'title {{title}}')
print(f"\\033[96m[Shad0wSploit] Watching session {sid} live output...\\033[0m")
print("=" * 60)
pos = 0
while True:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            fh.seek(pos)
            chunk = fh.read()
            if chunk:
                print(chunk, end='', flush=True)
                pos += len(chunk)
    except FileNotFoundError:
        pass
    time.sleep(0.3)
""")
        subprocess.Popen(
            ["cmd.exe", "/c", "start", f"\"{title}\"", "python", tail_script],
            shell=True
        )

    elif OS_NAME == "Linux":
        # Try common terminal emulators in priority order
        for term, args in [
            ("x-terminal-emulator", ["-e"]),
            ("xterm", ["-title", title, "-e"]),
            ("gnome-terminal", ["--title", title, "--"]),
            ("xfce4-terminal", ["--title", title, "-e"]),
            ("konsole", ["--title", title, "-e"]),
            ("lxterminal", ["--title", title, "-e"]),
        ]:
            if shutil.which(term):
                cmd = [term] + args + ["tail", "-f", logf]
                try:
                    subprocess.Popen(cmd)
                    return
                except Exception:
                    continue
        # Fallback: tmux or screen
        if shutil.which("tmux"):
            subprocess.Popen(["tmux", "new-window", f"tail -f {logf}"])

    elif OS_NAME == "Darwin":  # macOS
        apple_script = f"""
tell application "Terminal"
    do script "tail -f '{logf}'"
    activate
end tell
"""
        subprocess.Popen(["osascript", "-e", apple_script])


# ─── Client helpers ───────────────────────────────────────────────────────────

def _start_session(show_window=False):
    sid = str(uuid.uuid4())[:8]

    # Launch background server
    proc = subprocess.Popen(
        [sys.executable, __file__, SERVER_FLAG, sid],
        creationflags=(subprocess.CREATE_NO_WINDOW if OS_NAME == "Windows" else 0),
        close_fds=True
    )

    # Wait for alive flag
    alive = _alive(sid)
    deadline = time.time() + 12
    while not os.path.exists(alive):
        if time.time() > deadline:
            break
        time.sleep(0.25)

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions(session_id,created_at,last_used,status,pid,sess_dir,platform) VALUES(?,?,?,'active',?,?,?)",
        (sid, now, now, proc.pid, _sdir(sid), OS_NAME)
    )
    conn.commit()
    conn.close()

    if show_window:
        # Small delay so log file exists
        time.sleep(0.5)
        _launch_visible_window(sid)

    return sid, proc.pid


def _send_command(sid, command, timeout_secs=None):
    rq    = _req(sid)
    rp    = _resp(sid)
    alive = _alive(sid)

    if not os.path.exists(alive):
        return None, -1, "Server process for this session has died. Use --new-session to start a fresh shell."

    if os.path.exists(rp):
        os.remove(rp)

    with open(rq, "w", encoding="utf-8") as f:
        json.dump({"command": command}, f)

    start = time.time()
    while not os.path.exists(rp):
        if timeout_secs is not None and (time.time() - start) > timeout_secs:
            return None, -1, f"Timeout: command did not complete within {timeout_secs}s."
        time.sleep(0.2)

    with open(rp, "r", encoding="utf-8") as f:
        data = json.load(f)
    os.remove(rp)
    return data.get("output", ""), data.get("rc", 0), None


def _list_sessions():
    conn = get_db()
    rows = conn.execute(
        "SELECT session_id,created_at,last_used,status,pid,platform FROM sessions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _kill_session(sid):
    with open(_kill(sid), "w") as f:
        f.write("1")
    conn = get_db()
    conn.execute("UPDATE sessions SET status='terminated' WHERE session_id=?", (sid,))
    conn.commit()
    conn.close()


def _validate(sid):
    conn = get_db()
    row = conn.execute("SELECT status FROM sessions WHERE session_id=?", (sid,)).fetchone()
    conn.close()
    if not row:
        return False, f"Session '{sid}' not found."
    if row["status"] == "terminated":
        return False, f"Session '{sid}' was terminated."
    return True, None


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Internal server dispatch
    if len(sys.argv) >= 3 and sys.argv[1] == SERVER_FLAG:
        _run_server(sys.argv[2])
        return

    init_db()

    parser = argparse.ArgumentParser(
        description=(
            "Advanced Persistent Shell — keeps ONE shell alive across calls. "
            f"Auto-detected platform: {OS_NAME}. "
            "State (env vars, cwd, tool sessions like msfconsole) is preserved."
        )
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--new-session",   action="store_true", help="Start new persistent shell session")
    grp.add_argument("--list-sessions", action="store_true", help="List all sessions")
    grp.add_argument("--session-id",    type=str,            help="Target an existing session")

    parser.add_argument("--command",      type=str,            help="Command to run in session")
    parser.add_argument("--kill-session", action="store_true", help="Terminate the session")
    parser.add_argument("--show-window",  action="store_true",
                        help="Open a visible terminal window showing live session output")
    parser.add_argument("--timeout",      type=int, default=None,
                        help="Max seconds to wait for output (default: unlimited)")
    args = parser.parse_args()

    try:
        # ── New session ──────────────────────────────────────────────────────
        if args.new_session:
            sid, pid = _start_session(show_window=args.show_window)
            msg = (
                f"Persistent {OS_NAME} shell started (ID: {sid}, PID: {pid}). "
                f"Use --session-id {sid} --command \"<cmd>\" to run commands. "
                "All state (env vars, cwd, interactive tools like msfconsole) persists. "
            )
            if args.show_window:
                msg += "A visible terminal window has been opened to show live output."
            print(json.dumps({
                "status": "success", "action": "new_session",
                "session_id": sid, "pid": pid, "platform": OS_NAME,
                "message": msg
            }, ensure_ascii=False))
            return

        # ── List sessions ────────────────────────────────────────────────────
        if args.list_sessions:
            sessions = _list_sessions()
            print(json.dumps({
                "status": "success", "action": "list_sessions",
                "sessions": sessions, "total": len(sessions)
            }, ensure_ascii=False))
            return

        # ── Session-based actions ────────────────────────────────────────────
        sid = args.session_id

        if args.kill_session:
            ok, err = _validate(sid)
            if not ok:
                print(json.dumps({"status": "error", "message": err}))
                return
            _kill_session(sid)
            print(json.dumps({
                "status": "success", "action": "kill_session",
                "session_id": sid, "message": "Session terminated."
            }))
            return

        if args.show_window:
            # Open visible window for an existing session
            ok, err = _validate(sid)
            if not ok:
                print(json.dumps({"status": "error", "message": err}))
                return
            _launch_visible_window(sid)
            print(json.dumps({
                "status": "success", "action": "show_window",
                "session_id": sid,
                "message": f"Visible output window opened for session {sid}."
            }))
            return

        if args.command:
            ok, err = _validate(sid)
            if not ok:
                print(json.dumps({"status": "error", "message": err}))
                return

            output, rc, err_msg = _send_command(sid, args.command, timeout_secs=args.timeout)
            if err_msg:
                print(json.dumps({
                    "status": "error", "session_id": sid,
                    "command": args.command, "message": err_msg
                }))
                return

            print(json.dumps({
                "status": "success" if rc == 0 else "error_code",
                "action": "run_command",
                "session_id": sid,
                "command": args.command,
                "stdout": output,
                "return_code": rc,
                "platform": OS_NAME,
                "note": (
                    "Shell state (env vars, cwd, active tool sessions) persists. "
                    "Use --show-window to watch output live."
                )
            }, ensure_ascii=False))
            return

        parser.print_help()

    except Exception as e:
        print(json.dumps({
            "status": "error", "message": str(e),
            "traceback": traceback.format_exc()
        }))


if __name__ == "__main__":
    main()
