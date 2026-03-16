import os
import sys
import json
import subprocess
import sqlite3
import requests
import logging
import threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.status import Status
from rich.text import Text
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

from memory.memory_manager import MemoryManager

# --- Global Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
LOG_FILE = os.path.join(BASE_DIR, "agent_processing.log")

# Setup Global Processing Log
logging.basicConfig(
    filename=LOG_FILE,
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
   [ AUTONOMOUS AI AGENT - API C2 NODE ] [ v1.0 ]
    """
    console.print(Panel(Text(banner, style="bold red", justify="center"), border_style="red"))

def build_system_prompt():
    prompt = """You are SHAD0WSPLOIT, an elite, autonomous AI Assistant functioning as a Master Security Researcher and Systems Engineer.
You have full access to a powerful suite of command-line tools and a persistent memory management system.

Your goal is to complete the user's task step-by-step using a rigorous continuous feedback loop.
At each turn:
1. Review the overall MAIN GOAL.
2. Review the OUTPUT of the LAST executed tool.
3. Determine the SINGLE exact next logical step.
4. Execute that step.

============================
   AVAILABLE SYSTEM TOOLS
============================
All tools are standalone `.py` scripts. You MUST pass the exact flags they require. 
When you execute a tool, the system will run it and return the exact terminal output directly back to you in the next prompt.

[1. System & Core Tools]
- `get_time.py`: Returns current time. (Usage: `get_time.py --timezone "UTC"`)
- `run_shell.py`: Executes a terminal command safely. (Usage: `run_shell.py --command "ls -la"`)
- `file_manager.py`: Performs file operations. (Usage: `file_manager.py --action read --path "test.txt"` or `--action write` with `--content "..."`)
- `process_manager.py`: Lists/kills processes. (Usage: `process_manager.py --action list` or `--action kill --pid 1234`)

[2. Web & Search Tools]
- `web_search.py`: Performs a DuckDuckGo search. (Usage: `web_search.py --query "cyber threats"`)
- `fetch_url.py`: Scrapes text from a URL. (Usage: `fetch_url.py --url "https://example.com"`)
- `api_requester.py`: Makes HTTP requests. (Usage: `api_requester.py --method GET --url "..." --headers '{"Auth": "Key"}'`)
- `browser_simulator.py`: Launches a headless browser to render dynamic pages and extracts text. (Usage: `browser_simulator.py --url "https://example.com" --scroll`)

[3. Execution & Development Tools]
- `python_repl.py`: Runs Python code in an isolated environment. (Usage: `python_repl.py --code "print(2+2)"`)
- `go_runner.py`: Compiles and runs a .go file. (Usage: `go_runner.py --file "script.go"`)
- `git_manager.py`: Executes git commands. (Usage: `git_manager.py --repo_path "." --action status`)

[4. Networking & Security Tools]
- `port_scanner.py`: Scans ports on an IP. (Usage: `port_scanner.py --ip "192.168.1.1" --ports "80,443"`)
- `dns_lookup.py`: Retrieves DNS records. (Usage: `dns_lookup.py --domain "example.com"`)
- `packet_analyzer.py`: Captures N network packets. (Usage: `packet_analyzer.py --count 10`)
- `firewall_manager.py`: Modifies firewall rules. (Usage: `firewall_manager.py --action block --ip "10.0.0.5"`)
- `honeypot.py`: Sets up a listener to log malicious incoming packets. (Usage: `honeypot.py --port 8080 --log "honey.log"`)

[5. Memory & State Tools]
- `kv_store.py`: A local JSON key-value store. (Usage: `kv_store.py --action set --key "ip" --value "1.1.1.1"`)
- `memory_manager.py`: Extremely important module for persistence. You MUST use this tool to write important findings to memory. (Usage: `memory_manager.py save_deduction <task_id> "Your deduction text here"`)

[6. Custom Tool Creation]
- If a tool you need is NOT listed above, you have FULL PERMISSION to create it.
- Use `file_manager.py` (with `--action write` and `--path "tools/your_tool.py"`) to script the new tool in Python. 
- The tool must parse required arguments (e.g., via argparse) and print its output to stdout.
- Once created, you can immediately execute it like any other built-in tool (e.g., `"action": "your_tool.py"`).

[7. Self-Healing & Debugging Code]
- If you face a framework crash, JSON parsing error, or a broken tool, YOU HAVE PERMISSION TO FIX IT.
- Use `file_manager.py` (with `--action read` and `--path "main_agent.py"`) to read the problematic code.
- Write scripts using `file_manager.py --action write` to fix the bug.
- Once fixed, retry your action!

[8. GUI & Desktop Automation (Vision + Mouse/Keyboard)]
- `gui_vision.py`: Takes a screenshot of the desktop, optionally launches an app first, and sends it to the Ollama vision model (`gpt-oss`) to find elements or buttons. Returns the screen resolution and the AI's analysis. (Usage: `gui_vision.py --prompt "Find the login button coordinates in JSON format"` or `gui_vision.py --app "notepad" --prompt "Find the text box"`)
- `gui_mouse.py`: Controls the mouse and keyboard to interact with the GUI based on coordinates found by `gui_vision.py`. (Usage: `gui_mouse.py --action click --x 500 --y 300` or `gui_mouse.py --action type --text "hello"` or `gui_mouse.py --action press --key "enter"`)

[9. Network & Security Tools]
- `port_scanner.py`: Scans ports on an IP. (Usage: `port_scanner.py --ip "192.168.1.1" --ports "80,443"`)
- `dns_lookup.py`: Retrieves DNS records. (Usage: `dns_lookup.py --domain "example.com"`)
- `packet_analyzer.py`: Captures N network packets. (Usage: `packet_analyzer.py --count 10`)
- `firewall_manager.py`: Modifies firewall rules. (Usage: `firewall_manager.py --action block --ip "10.0.0.5"`)
- `honeypot.py`: Sets up a listener to log malicious incoming packets. (Usage: `honeypot.py --port 8080 --log "honey.log"`)

[10. Notes]:
- Important notes: If you're conducting a hacking operation and haven't found a vulnerability or solution, remember the saying "nothing is impossible." Search for subdomains and try to hack them. If you reach them, you'll reach the network and from there the target. If you're in the middle of writing code, remember that it must be clean and organized. Combine multiple files if necessary to make it clean, organized, creative, and strong code without vulnerabilities.
- Professionalism: Maintain a strictly professional, objective, and analytical tone in all outputs. Avoid unnecessary verbosity or filler text.
- Reliability & Safety: Gracefully handle exceptions, invalid inputs, and unexpected errors without crashing. Always prioritize system stability and user safety during operations.
- Audit & Accountability: Ensure all actions, findings, and errors are accurately logged to provide a clear and comprehensive audit trail.
- Precision: Validate all data, inputs, and outputs to ensure integrity, security, and exactness in every task.
- When providing an opinion on a decision, systematically assess all practical alternatives. For each alternative, map out the full chain of cause-and-effect outcomes, including risks, benefits, and secondary impacts. Conclude by selecting the option with the highest likelihood of achieving the desired result, grounded in a realistic real-world context rather than abstract speculation.

CRITICAL MEMORY INSTRUCTION: Whenever you execute ANY tool and discover new information, your NEXT action MUST be to use the `memory_manager.py` tool to write what you learned before proceeding to the next logical step. In your arguments, exactly write "<task_id>" and the framework will automatically inject the actual ID.

============================
   CRITICAL FORMAT INSTRUCTION
============================
You MUST respond ONLY with a strict JSON object in this EXACT order. Do NOT output markdown ticks or conversational text outside this JSON block.
{
  "state_review": "Analyze the result of the previous step. What does it mean?",
  "goal_alignment": "How close are we to the final goal?",
  "thought": "Your reasoning for what EXACT step you need to take right now.",
  "action": "The exact tool filename from the tools/ directory (e.g., 'run_shell.py'). If the overall GOAL is FINISHED, output 'FINISH'.",
  "args": ["--arg1", "value1"]
}

If your action is "FINISH", your args MUST be: ["--answer", "Your final detailed answer here"].
"""
    return prompt

def call_llm(system_prompt, dynamic_context):
    """
    Calls the local Ollama LLM API with strict JSON enforcement.
    """
    url = "http://localhost:11434/api/generate"
    model = "huihui_ai/gpt-oss-abliterated:latest"
    
    full_prompt = f"{system_prompt}\n\n{dynamic_context}"
    
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }
    
    logging.info(f"Sending request to Ollama ({model})...")
    
    try:
        response = requests.post(url, json=payload, timeout=1200)
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "{}")
        
        if not response_text or response_text.strip() == "":
            response_text = '{"state_review": "Error", "goal_alignment": "Error", "thought": "The model returned an empty string.", "action": "run_shell.py", "args": ["--command", "echo retry"]}'
        
        logging.info("Received response from Ollama successfully.")
        
        import re
        
        # --- Print Raw LLM Output Debug ---
        console.print(Panel(response_text, title="Raw LLM Output (Debug)", style="dim white"))
        
        # --- Aggressively Strip <think> tags ---
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
        response_text = re.sub(r'<think>.*', '', response_text, flags=re.DOTALL)
        
        # --- Robust Bracket Counting JSON Extraction ---
        start_idx = response_text.find('{')
        if start_idx != -1:
            brace_count = 0
            end_idx = -1
            for i, char in enumerate(response_text[start_idx:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = start_idx + i
                        break
            
            if end_idx != -1:
                clean_json_str = response_text[start_idx:end_idx+1]
            else:
                clean_json_str = response_text.strip()
        else:
            clean_json_str = response_text.strip()
            
        clean_json_str = clean_json_str.strip()
        while clean_json_str.startswith('{{'):
            clean_json_str = clean_json_str[1:]
        while clean_json_str.endswith('}}'):
            clean_json_str = clean_json_str[:-1]

        clean_json_str = re.sub(r',\s*}', '}', clean_json_str)
        clean_json_str = re.sub(r',\s*]', ']', clean_json_str)
        
        try:
            json.loads(clean_json_str)
            return clean_json_str
        except json.JSONDecodeError as jde:
            if "'" in clean_json_str and '"' not in clean_json_str[:50]:
                import ast
                try:
                    parsed_dict = ast.literal_eval(clean_json_str)
                    return json.dumps(parsed_dict)
                except Exception:
                    pass
            
            logging.error(f"Ollama returned invalid JSON. Err: {jde} | Raw output: {response_text}")
            return json.dumps({
                "error": f"CRITICAL: Invalid JSON format returned. You MUST fix your JSON output syntax. Make sure you only output JSON and it is fully closed. Raw JSON parsed attempt: {clean_json_str}"
            })
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection error: Could not reach Ollama API at {url}. Is Ollama running? Details: {str(e)}"
        logging.error(error_msg)
        console.print(Panel(error_msg, title="API Error", style="bold red"))
        return json.dumps({"error": error_msg})


def call_llm_text(system_prompt, prompt):
    """ Calls LLM to get a raw markdown/text string without JSON enforcement. """
    url = "http://localhost:11434/api/generate"
    model = "huihui_ai/gpt-oss-abliterated:latest"
    
    full_prompt = f"{system_prompt}\n\n{prompt}"
    payload = {"model": model, "prompt": full_prompt, "stream": False}
    
    try:
        response = requests.post(url, json=payload, timeout=1200)
        response.raise_for_status()
        result = response.json()
        import re
        text = result.get("response", "")
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return text.strip()
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"

def execute_tool(action, args):
    """Executes a tool script securely via subprocess and returns EXACT output/errors."""
    if action == "memory_manager.py":
        script_path = os.path.join(MEMORY_DIR, action)
    else:
        script_path = os.path.join(TOOLS_DIR, action)
        
    if not os.path.exists(script_path):
        err = f"Error: Tool '{action}' not found at {script_path}."
        logging.error(err)
        return 1, err
        
    cmd = [sys.executable, script_path] + args
    logging.info(f"Executing tool: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = process.stdout.strip()
        has_error = False
        
        if process.stderr.strip() or process.returncode != 0:
            output += f"\n[STDERR]: {process.stderr.strip()}"
            has_error = True
            
        if not output:
            output = f"Tool '{action}' executed but produced no output. Exit code: {process.returncode}"
            
        if has_error:
            recovered_error = f"TOOL EXECUTION FAILED (Exit {process.returncode}).\n{output}\nRead the error above and fix your arguments or approach."
            logging.warning(recovered_error)
            return process.returncode, recovered_error
            
        logging.info("Tool executed successfully.")
        return process.returncode, output
        
    except subprocess.TimeoutExpired:
        err = f"TOOL EXECUTION FAILED: Execution of {action} timed out after 120 seconds. Try a different approach."
        logging.error(err)
        return 1, err
    except Exception as e:
        err = f"TOOL EXECUTION FAILED: Critical exception while executing {action}: {str(e)}"
        logging.error(err)
        return 1, err


def handle_agent_request(user_message, send_update=None):
    def emit(u_type, data):
        if send_update:
            msg = json.dumps({"type": u_type, "data": data}, ensure_ascii=False) + "\n"
            send_update(msg)

    manager = MemoryManager()
    
    emit("status", f"Classifying user request: {user_message}")
    
    # 1. Automatic classification into New Task or Existing Task
    db_path = os.path.join(MEMORY_DIR, "master_tasks.db")
    tasks_info = []
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT task_id, name, description FROM tasks WHERE status != 'completed' ORDER BY last_updated DESC LIMIT 5")
            tasks = cursor.fetchall()
            conn.close()
            for t in tasks:
                tasks_info.append({"task_id": t[0], "name": t[1], "description": t[2]})
        except Exception:
            pass

    console.print(Panel(f"Classifying user request: {user_message}", style="cyan"))
            
    classify_prompt = f"""You are a task classifier for an AI agent.
The user has submitted this message via API request: "{user_message}"

Here are the previously started active tasks:
{json.dumps(tasks_info, indent=2)}

Determine if this message is a continuation of one of the EXISTING active tasks, or if it represents a totally NEW task altogether.
Respond ONLY with this exact JSON structure:
{{
  "is_new": true/false,
  "task_id": "the exact task_id from the list if old, or null if new",
  "name": "Pick a short 3-word name for this task if new",
  "goal": "A detailed explanation of the new goal/directive based on what the user wants if new"
}}"""

    classification_response = call_llm("Respond ONLY in JSON. Follow instructions.", classify_prompt)
    
    is_new = True
    assigned_task_id = None
    goal = user_message
    
    try:
        class_data = json.loads(classification_response)
        is_new = class_data.get("is_new", True)
        goal = class_data.get("goal", user_message)
        
        if not is_new and class_data.get("task_id"):
            assigned_task_id = class_data.get("task_id")
            console.print(f"[bold green]Resuming Existing Task ID: {assigned_task_id}[/bold green]")
            emit("status", f"Resuming Existing Task ID: {assigned_task_id}")
            # Update the task directive in the database
            conn = sqlite3.connect(os.path.join(MEMORY_DIR, "master_tasks.db"))
            conn.execute("UPDATE tasks SET status = 'in_progress', description = description || ' -> ' || ? WHERE task_id = ?", (goal, assigned_task_id))
            conn.commit()
            conn.close()
        else:
            name = class_data.get("name", "API Task")
            result = manager.init_task(name, goal)
            assigned_task_id = result["task_id"]
            console.print(f"[bold green]Started New Task: {name} ({assigned_task_id})[/bold green]")
            emit("status", f"Started New Task: {name} ({assigned_task_id})")
            
    except Exception as e:
        console.print(f"[bold yellow]Classification fallback due to JSON error.[/bold yellow]")
        name = "API Driven Task"
        result = manager.init_task(name, goal)
        assigned_task_id = result["task_id"]
        console.print(f"[bold green]Started New Task: {name} ({assigned_task_id})[/bold green]")
        emit("status", f"Started New Task: {name} ({assigned_task_id}) (Fallback)")

    logging.info(f"API Request mapped to Task: {assigned_task_id}")
    
    system_prompt = build_system_prompt()
    collected_actions = []
    loop_interrupted = False
    
    resume_data = manager.get_resume_state(assigned_task_id)
    recent_logs = resume_data.get("recent_logs", [])
    if recent_logs:
        last_log = recent_logs[-1]
        last_tool_output = f"Resumed Session via API. User update: '{goal}'. Previous tool '{last_log['action']}' returned:\n{last_log['details']}"
    else:
        last_tool_output = f"New task started via API. Initial user request: '{goal}'. Start exploring and executing the goal."

    # Max iteration limit to avoid infinite loops hanging the API caller forever
    max_steps = 15
    step_count = 0
    
    while step_count < max_steps:
        try:
            step_count += 1
            resume_data = manager.get_resume_state(assigned_task_id)
            recent_logs = resume_data.get("recent_logs", [])
            logs_str = ""
            for log in recent_logs[-5:]:
                logs_str += f"- [{log['timestamp']}] Action: {log['action']} | Status: {log['status']} | Details: {log['details'][:150]}...\n"
                
            turn_prompt = (
                f"================================================\n"
                f"                 CURRENT CONTEXT\n"
                f"================================================\n"
                f"[CURRENT TASK ID]: {assigned_task_id}\n"
                f"[ONGOING TASK DIRECTIVE]: {goal}\n\n"
                f"--- HISTORICAL ACTIONS ---\n"
                f"{logs_str}\n"
                f"--- RESULT OF PREVIOUS STEP ---\n"
                f"{last_tool_output}\n"
                f"================================================\n"
                f"Review the previous result, compare to the Goal, and execute the NEXT LOGICAL STEP."
            )
            
            with Status(f"[bold cyan]Agent processing step {step_count}...[/bold cyan]", console=console, spinner="bouncingBar"):
                emit("status", f"Thinking... (Step {step_count})")
                llm_response = call_llm(system_prompt, turn_prompt)
                
            try:
                action_data = json.loads(llm_response.strip())
                collected_actions.append({
                    "step": step_count,
                    "review": action_data.get("state_review"),
                    "validation": action_data.get("goal_alignment"),
                    "thought": action_data.get("thought")
                })
                
                action_script = action_data.get("action", "")
                action_args = action_data.get("args", [])
                
                thought_text = action_data.get('thought', 'None')
                console.print(Panel(f"[bold white]Thought:[/bold white] {thought_text}", title="🧠 Reasoning", style="cyan"))
                emit("thought", thought_text)
                
                if action_script == "FINISH":
                    final_ans = action_args[1] if (len(action_args) >= 2 and action_args[0] == "--answer") else "Task operations completed by agent."
                    manager.log_action(assigned_task_id, "FINISH", "completed", final_ans)
                    collected_actions.append({"final_result": final_ans})
                    emit("finish", final_ans)
                    
                    conn = sqlite3.connect(os.path.join(MEMORY_DIR, "master_tasks.db"))
                    conn.execute("UPDATE tasks SET status = 'completed' WHERE task_id = ?", (assigned_task_id,))
                    conn.commit()
                    conn.close()
                    break
                    
                if "error" in action_data and action_data["error"].startswith("CRITICAL"):
                    last_tool_output = action_data["error"]
                    emit("error", last_tool_output)
                    continue
                    
                cmd_str = f"{action_script} {' '.join(action_args)}"
                console.print(Panel(f"[bold yellow]> {cmd_str}[/bold yellow]", title="⚡ Tool Execution"))
                emit("action", cmd_str)
                
                action_args_replaced = [arg.replace("<task_id>", assigned_task_id) for arg in action_args]
                return_code, tool_output = execute_tool(action_script, action_args_replaced)
                
                manager.log_action(assigned_task_id, action_script, "success" if return_code == 0 else "error", tool_output)
                collected_actions.append({"tool_ran": action_script, "output": tool_output[:500]})
                
                emit("action_result", {"tool": action_script, "output": tool_output, "return_code": return_code})
                last_tool_output = f"Output of '{action_script}':\n{tool_output}"
                
            except json.JSONDecodeError:
                err_str = "SYSTEM ERROR: Your previous response was NOT valid JSON."
                emit("error", err_str)
                last_tool_output = err_str
                
        except KeyboardInterrupt:
            # Caught Ctrl+C during processing
            console.print("\n[bold red][!] Shutting down... Loop aborted manually via Ctrl+C. Summarizing progress...[/bold red]")
            loop_interrupted = True
            break
        except Exception as e:
            console.print(f"[bold red]Loop error: {str(e)}[/bold red]")
            break

    # Summarize final aggregated message as requested
    console.print("[bold cyan]Agent completed steps or was interrupted. Compiling the final response message...[/bold cyan]")
    emit("status", "Agent completed steps. Compiling final summary...")
    
    summary_sys_prompt = "You are an AI reporting assistant that translates dense technical execution logs into a clean, understandable message."
    summary_user_prompt = f"""
The user submitted this original request via API:
"{user_message}"

The system agent executed these steps in response:
{json.dumps(collected_actions, indent=2)}

Please analyze the sequence of actions and the final state.
Write a highly organized, professional summary message explaining to the user what was determined, what tools were used, and the final outcomes.
Format nicely using Markdown text. 
If no final answer is reached yet because it was interrupted or hit a limit, clearly state the current progress and findings.
DO NOT use JSON. State your answer in a natural conversational text.
"""
    
    final_organized_message = call_llm_text(summary_sys_prompt, summary_user_prompt)
    
    if loop_interrupted:
        final_organized_message = "🔴 **[Process Stopped - Shutting Down]** (Process interrupted manually via Ctrl+C)\n\n" + final_organized_message
        
    emit("summary", final_organized_message)
    return final_organized_message, loop_interrupted


class C2RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Prevent spamming the stdout with GET/POST access logs to keep terminal clean
        pass
        
    def end_headers(self):
        # We also want to support CORS if they want to call this from a browser script
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/task':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                user_msg = data.get('message', '')
                
                if not user_msg:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"status": "error", "message": "Missing required field: message"}')
                    return
                
                console.print(Panel(f"[bold white]Received Request:[/bold white] {user_msg}", title="📥 API INBOUND", style="green"))
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json-lines; charset=utf-8')
                self.send_header('Transfer-Encoding', 'chunked')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                def stream_update(data_str):
                    try:
                        encoded = data_str.encode('utf-8')
                        self.wfile.write(f"{len(encoded):X}\r\n".encode('utf-8'))
                        self.wfile.write(encoded)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                    except Exception as e:
                        logging.error(f"Stream error: {e}")

                response_text, interrupted = handle_agent_request(user_msg, send_update=stream_update)
                
                try:
                    self.wfile.write(b"0\r\n\r\n")
                    self.wfile.flush()
                except Exception:
                    pass
                
                if interrupted:
                    console.print("[bold red]API response delivered successfully. Proceeding to shut down server as per Ctrl+C request...[/bold red]")
                    # Shutdown asynchronously to allow the socket to flush the HTTP response back first
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    
            except Exception as e:
                try:
                    err_payload = json.dumps({"type": "error", "data": f"Server error: {str(e)}"}, ensure_ascii=False) + "\n"
                    encoded = err_payload.encode('utf-8')
                    self.wfile.write(f"{len(encoded):X}\r\n".encode('utf-8'))
                    self.wfile.write(encoded)
                    self.wfile.write(b"\r\n0\r\n\r\n")
                    self.wfile.flush()
                except Exception:
                    pass
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"status": "error", "message": "Endpoint not found. Use POST /api/task"}')

def main():
    print_banner()
    port = 8080
    server_address = ('0.0.0.0', port)
    
    try:
        httpd = HTTPServer(server_address, C2RequestHandler)
        console.print(f"[bold green][+] C2 API Node initialized successfully.[/bold green]")
        console.print(f"[bold green][+] Listening for requests locally on http://127.0.0.1:{port}/api/task[/bold green]")
        console.print(f"[bold cyan][!] Agent will run silently until an API payload is received. Press Ctrl+C at any time to abort the server.[/bold cyan]\n")
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[bold red][!] Shutting down... Server gracefully terminating. Goodbye.[/bold red]")
        if 'httpd' in locals():
            httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    main()
