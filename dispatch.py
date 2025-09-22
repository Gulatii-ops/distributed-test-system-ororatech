"""
Simple dispatcher script that 
    - Sends tasks concurrently to two queues (via task routing in celery_app.py).
    - Structured JSON logging for transparency (console + timestamped file in /logs).
    - A simple progress visualization using tqdm to show task completion.
    - End-of-run ASCII table summarizing results and per-task durations with colors.
"""

import json
import logging
import time
from tqdm import tqdm
from pathlib import Path
from celery_app import task_a, task_b
from colorama import init, Fore, Style, Back

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Prepare log folder and file for storing JSON results
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)  # Create 'logs' folder if missing
timestamp = time.strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"log_{timestamp}.json"

# Logger setup for console 
logger = logging.getLogger("task_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def log_json(event: str, **kwargs):
    """
    Logs plain JSON to console and saves the same to a timestamped file.
    """
    entry = {"event": event, "details": kwargs}
    line = json.dumps(entry, ensure_ascii=False)

    # Console
    logger.info(line)

    # File
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_status_color(status: str) -> str:
    """
    Returns appropriate color codes for different task statuses.
    """
    color_map = {
        "success": Fore.GREEN,
        "failure": Fore.RED,
        "timeout": Fore.MAGENTA,
        "unknown": Fore.YELLOW,
        "pending": Fore.YELLOW,
        "running": Fore.CYAN
    }
    return color_map.get(status.lower(), Fore.WHITE)

def get_duration_color(duration: float) -> str:
    """
    Returns color based on task duration (green for fast, yellow for medium, red for slow).
    """
    if duration < 1.0:
        return Fore.GREEN
    elif duration < 5.0:
        return Fore.YELLOW
    else:
        return Fore.RED

def print_summary_table(results: dict, task_times: dict, statuses: dict):
    """
    Prints a colorized ASCII table with task name, status, duration, and result.
    """
    if not results:
        print(f"{Fore.YELLOW}No results to display{Style.RESET_ALL}")
        return

    # Column widths
    name_w = max(len("task"), *(len(k) for k in results)) + 2
    status_w = max(len("status"), 6) + 2
    time_w = max(len("time_s"), 6) + 2
    result_w = 60  # cap result text width

    def colored_row(task, status, duration, result):
        """Create a colored row for the table."""
        result_str = str(result)

        if len(result_str) > result_w:
            result_str = result_str[:result_w - 3] + "..."

        # Apply colors
        status_color = get_status_color(status)
        duration_color = get_duration_color(duration)

        # Color the result based on status
        if status.lower() == "success":
            result_color = Fore.GREEN
        elif status.lower() in ["failure", "timeout"]:
            result_color = Fore.RED
        else:
            result_color = Fore.WHITE

        return (f"{Fore.CYAN}{task:<{name_w}}{Style.RESET_ALL}"
                f"{status_color}{status:<{status_w}}{Style.RESET_ALL}"
                f"{duration_color}{duration:<{time_w}}{Style.RESET_ALL}"
                f"{result_color}{result_str}{Style.RESET_ALL}")

    # Header with styling
    header = (f"{Style.BRIGHT}{Fore.WHITE}{'task':<{name_w}}"
              f"{'status':<{status_w}}{'time_s':<{time_w}}result{Style.RESET_ALL}")
    separator = f"{Fore.MAGENTA}{'-' * (name_w + status_w + time_w + result_w)}{Style.RESET_ALL}"

    print(f"\n{header}")
    print(separator)

    for task_name in results:
        status = statuses.get(task_name, "unknown")
        duration_val = task_times.get(task_name, 0.0)
        duration_str = f"{duration_val:.3f}"
        print(colored_row(task_name, status, duration_val, results[task_name]))

    # Add a bottom border
    print(separator)

def main():
    overall_start = time.time()
    print()

    log_json("start", message="Dispatching tasks")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🚀 Starting task dispatch...{Style.RESET_ALL}\n")

    # Dispatch tasks and record start times

    start_times = {}
    tasks = {
        "task_a": task_a.delay(),
        "task_b": task_b.delay(),
    }

    for name in tasks:
        start_times[name] = time.time()

    total = len(tasks)
    success_count = 0
    results = {}
    task_times = {}   # per-task durations
    statuses = {}     # per-task status

    # Progress bar visualization with timeout handling
    TASK_TIMEOUT = 30  # Maximum time to wait for any single task (in seconds)
    CHECK_INTERVAL = 0.5  # How often to check task status (in seconds)

    with tqdm(total=total, desc="Processing", ncols=80, 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        completed = 0
        while completed < total:
            current_time = time.time()

            for name, result in list(tasks.items()):
                task_runtime = current_time - start_times[name]
                # Check if task has completed
                if result.ready():
                    end_time = time.time()
                    duration = round(end_time - start_times[name], 3)
                    try:
                        output = result.get(timeout=20)
                        status = "success"
                        success_count += 1
                    except Exception as e:
                        output = str(e)
                        status = "failure"

                    results[name] = output
                    task_times[name] = duration
                    statuses[name] = status

                    # Log JSON for each completed task
                    print("\n")
                    log_json(
                        "task_completed",
                        task=name,
                        status=status,
                        result=output,
                        execution_time_s=duration
                    )
                    del tasks[name]
                    completed += 1
                    pbar.update(1)

                # Check if task has timed out
                elif task_runtime > TASK_TIMEOUT:
                    end_time = time.time()
                    duration = round(end_time - start_times[name], 3)

                    # Try to revoke the task
                    try:
                        result.revoke(terminate=True)   # Force kill
                    except Exception:
                        pass  # Worker might already be down
                
                    status = "timeout"
                    output = f"Task timed out after {TASK_TIMEOUT}s (worker may be down)"

                    results[name] = output
                    task_times[name] = duration
                    statuses[name] = status

                    # Log timeout event
                    print("\n")
                    log_json(
                        "task_timeout",
                        task=name,
                        status=status,
                        result=output,
                        execution_time_s=duration,
                        timeout_threshold_s=TASK_TIMEOUT
                    )
                    del tasks[name]
                    completed += 1
                    pbar.update(1)

            time.sleep(CHECK_INTERVAL)
    overall_end = time.time()

    # ASCII table summary with colors
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}📊 EXECUTION SUMMARY{Style.RESET_ALL}")
    print_summary_table(results, task_times, statuses)
    print("\n")

    # Calculate summary metrics
    success_rate = round((success_count / total) * 100, 2)
    total_time = round(overall_end - overall_start, 3)

    # Colored summary stats
    if success_rate == 100:
        success_color = Fore.GREEN
        success_icon = "✅"
    elif success_rate >= 50:
        success_color = Fore.YELLOW
        success_icon = "⚠️"
    else:
        success_color = Fore.RED
        success_icon = "❌"
    print(f"{success_icon} {success_color}Success Rate: {success_rate}%{Style.RESET_ALL}")
    print(f"⏱️  {Fore.BLUE}Total Execution Time: {total_time}s{Style.RESET_ALL}")

    # Log summary and total time
    log_json("summary", total_tasks=total, success_rate=f"{success_rate}%", total_time_s=total_time)
    #log_json("end", message="All tasks completed", total_time_s=total_time)

    print(f"\n💾 {Fore.MAGENTA}Logs saved to: {log_file}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()