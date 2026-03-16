import argparse
import sqlite3
import json
import os
import uuid
import datetime
import csv
import traceback
import re
from pathlib import Path

# Base directory for memory management
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(MEMORY_DIR, "master_tasks.db")

class MemoryManager:
    def __init__(self):
        self._ensure_setup()

    def _ensure_setup(self):
        """Ensures the memory directory and master database exist."""
        os.makedirs(MEMORY_DIR, exist_ok=True)
        
        # Initialize SQLite master tasks database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                current_step INTEGER DEFAULT 0,
                folder_path TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def _get_timestamp(self):
        """Returns ISO 8601 formatted timestamp."""
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _safe_path(self, task_id, filename):
        """Ensures the file path is safely within the task's isolated directory to prevent traversal attacks."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT folder_path FROM tasks WHERE task_id = ?', (task_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            raise ValueError(f"Task ID '{task_id}' not found.")
            
        folder_path = result[0]
        
        # Prevent directory traversal
        clean_filename = os.path.basename(filename)
        safe_file_path = os.path.join(folder_path, clean_filename)
        
        # Double check resolution
        if not os.path.abspath(safe_file_path).startswith(os.path.abspath(folder_path)):
            raise PermissionError("Path traversal detected.")
            
        return safe_file_path

    def _update_timestamp(self, task_id, current_step=None):
        """Updates the last_updated timestamp for a task."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = self._get_timestamp()
        
        if current_step is not None:
            cursor.execute('UPDATE tasks SET last_updated = ?, current_step = ? WHERE task_id = ?', 
                         (now, current_step, task_id))
        else:
            cursor.execute('UPDATE tasks SET last_updated = ? WHERE task_id = ?', 
                         (now, task_id))
        conn.commit()
        conn.close()

    def init_task(self, name, description=""):
        """Initializes a new task workspace."""
        task_id = str(uuid.uuid4())
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name).strip('_')
        folder_name = f"task_{task_id}_{safe_name}"
        folder_path = os.path.join(MEMORY_DIR, folder_name)
        
        os.makedirs(folder_path, exist_ok=True)
        
        # Initialize basic files
        plan_path = os.path.join(folder_path, "plan.json")
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump({"steps": [], "current_index": 0}, f, indent=4)
            
        logs_path = os.path.join(folder_path, "logs.csv")
        with open(logs_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Action", "Status", "Details"])
            
        deductions_path = os.path.join(folder_path, "deductions.json")
        with open(deductions_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)

        now = self._get_timestamp()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (task_id, name, description, status, created_at, last_updated, current_step, folder_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, name, description, "initialized", now, now, 0, folder_path))
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "task_id": task_id,
            "folder_path": folder_path,
            "message": f"Task '{name}' initialized successfully."
        }

    def update_plan(self, task_id, plan_json_str):
        """Updates the plan.json file for a task."""
        try:
            plan_data = json.loads(plan_json_str)
            if "steps" not in plan_data:
                plan_data = {"steps": plan_data, "current_index": 0}
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON provided for plan.")

        plan_path = self._safe_path(task_id, "plan.json")
        
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=4)
            
        current_step = plan_data.get("current_index", 0)
        self._update_timestamp(task_id, current_step=current_step)
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Plan updated successfully."
        }

    def log_action(self, task_id, action, status, details):
        """Appends an action to the task's logs.csv."""
        logs_path = self._safe_path(task_id, "logs.csv")
        now = self._get_timestamp()
        
        # Handle newlines or commas in details to prevent CSV breaking
        if details:
            details = str(details).replace("\n", " ").replace("\r", " ")
            
        with open(logs_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([now, action, status, details])
            
        self._update_timestamp(task_id)
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Action logged successfully."
        }

    def save_deduction(self, task_id, text):
        """Appends a new deduction to deductions.json."""
        deductions_path = self._safe_path(task_id, "deductions.json")
        
        try:
            with open(deductions_path, 'r', encoding='utf-8') as f:
                deductions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            deductions = []
            
        deduction_entry = {
            "timestamp": self._get_timestamp(),
            "text": text
        }
        
        deductions.append(deduction_entry)
        
        with open(deductions_path, 'w', encoding='utf-8') as f:
            json.dump(deductions, f, indent=4)
            
        self._update_timestamp(task_id)
        
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Deduction saved successfully."
        }

    def get_resume_state(self, task_id):
        """Returns a comprehensive summary to resume exactly where the agent left off."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, description, status, created_at, last_updated, current_step, folder_path 
            FROM tasks WHERE task_id = ?
        ''', (task_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            raise ValueError(f"Task ID '{task_id}' not found.")
            
        name, desc, status, created, updated, current_step, folder = result
        
        # Read plan
        plan_path = self._safe_path(task_id, "plan.json")
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
        except Exception:
            plan_data = {"steps": [], "current_index": current_step}
            
        # Read recent deductions (last 3)
        deductions_path = self._safe_path(task_id, "deductions.json")
        try:
            with open(deductions_path, 'r', encoding='utf-8') as f:
                all_deductions = json.load(f)
                recent_deductions = all_deductions[-3:] if all_deductions else []
        except Exception:
            recent_deductions = []
            
        # Read logs for recent detailed context and ALL actions for history
        logs_path = self._safe_path(task_id, "logs.csv")
        recent_logs = []
        action_history = []
        try:
            with open(logs_path, 'r', encoding='utf-8') as f:
                lines = list(csv.reader(f))[1:]  # skip header
                
                # Extract full brief history
                action_history = [
                    f"[{l[0]}] {l[1]} (Status: {l[2]})"
                    for l in lines
                ]
                
                # Extract recent 50 detailed logs
                recent_logs_raw = lines[-50:] if lines else []
                recent_logs = [
                    {"timestamp": l[0], "action": l[1], "status": l[2], "details": l[3] if len(l) > 3 else ""}
                    for l in recent_logs_raw
                ]
                # Format to dicts for JSON output
                recent_logs = [
                    {"timestamp": l[0], "action": l[1], "status": l[2], "details": l[3] if len(l) > 3 else ""}
                    for l in recent_logs
                ]
        except Exception:
            pass

        return {
            "status": "success",
            "task_info": {
                "task_id": task_id,
                "name": name,
                "description": desc,
                "status": status,
                "created_at": created,
                "last_updated": updated,
                "current_step": current_step
            },
            "plan_state": plan_data,
            "recent_deductions": recent_deductions,
            "action_history": action_history,
            "recent_logs": recent_logs
        }

    def get_global_memory(self):
        """Retrieves deductions from ALL completed tasks to provide global cross-task memory."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT task_id, name, folder_path FROM tasks WHERE status = 'completed'")
        completed_tasks = cursor.fetchall()
        conn.close()

        global_knowledge = []
        for t_id, t_name, t_folder in completed_tasks:
            deductions_path = os.path.join(t_folder, "deductions.json")
            try:
                if os.path.exists(deductions_path):
                    with open(deductions_path, 'r', encoding='utf-8') as f:
                        deductions = json.load(f)
                        if deductions:
                            global_knowledge.append({
                                "task_name": t_name,
                                "task_id": t_id,
                                "lessons_learned": deductions
                            })
            except Exception:
                continue

        return {
            "status": "success",
            "global_knowledge": global_knowledge
        }


def main():
    parser = argparse.ArgumentParser(description="Memory and State Management CLI for Autonomous AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init Command
    init_parser = subparsers.add_parser("init", help="Initialize a new task workspace")
    init_parser.add_argument("--name", required=True, help="Name of the task")
    init_parser.add_argument("--desc", default="", help="Optional description of the task")
    
    # Update Plan Command
    plan_parser = subparsers.add_parser("update_plan", help="Update the plan.json for a task")
    plan_parser.add_argument("--task_id", required=True, help="Task UUID")
    plan_parser.add_argument("--plan", required=True, help="JSON string representing the plan")
    
    # Log Command
    log_parser = subparsers.add_parser("log", help="Log an action to a task's logs.csv")
    log_parser.add_argument("--task_id", required=True, help="Task UUID")
    log_parser.add_argument("--action", required=True, help="Action performed")
    log_parser.add_argument("--status", required=True, help="Status of the action (e.g., success, error)")
    log_parser.add_argument("--details", default="", help="Details or output of the action")
    
    # Save Deduction Command
    deduct_parser = subparsers.add_parser("save_deduction", help="Save an agent thought or conclusion")
    deduct_parser.add_argument("--task_id", required=True, help="Task UUID")
    deduct_parser.add_argument("--text", required=True, help="Text of the deduction")
    
    # Resume Command
    resume_parser = subparsers.add_parser("resume", help="Get full resumable state of a task")
    resume_parser.add_argument("--task_id", required=True, help="Task UUID")
    
    # Global Memory Command
    global_parser = subparsers.add_parser("global_memory", help="Retrieve knowledge from all past completed tasks")
    
    args = parser.parse_args()
    
    # Initialize MemoryManager (will setup DB and folder space if not exists)
    try:
        manager = MemoryManager()
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Initialization failed: {str(e)}", "traceback": traceback.format_exc()}))
        return

    # No command provided
    if not args.command:
        parser.print_help()
        return

    try:
        result = {}
        if args.command == "init":
            result = manager.init_task(args.name, args.desc)
            
        elif args.command == "update_plan":
            result = manager.update_plan(args.task_id, args.plan)
            
        elif args.command == "log":
            result = manager.log_action(args.task_id, args.action, args.status, args.details)
            
        elif args.command == "save_deduction":
            result = manager.save_deduction(args.task_id, args.text)
            
        elif args.command == "resume":
            result = manager.get_resume_state(args.task_id)
            
        elif args.command == "global_memory":
            result = manager.get_global_memory()

        print(json.dumps(result))
        
    except ValueError as ve:
        error_result = {
            "status": "error",
            "error_type": "ValueError",
            "message": str(ve)
        }
        print(json.dumps(error_result))
    except PermissionError as pe:
        error_result = {
            "status": "error",
            "error_type": "PermissionError",
            "message": str(pe)
        }
        print(json.dumps(error_result))
    except Exception as e:
        error_result = {
            "status": "error",
            "error_type": "Exception",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
