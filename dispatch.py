"""
Simple dispatcher script that 
    - Sends tasks concurrently to two queues (via task routing in celery_app.py).
    - Structured JSON logging for transparency (console + timestamped file in /logs).
    - A simple progress visualization using tqdm to show task completion.
    - End-of-run ASCII table summarizing results and per-task durations.
"""

import json
import logging
import time
from tqdm import tqdm
from pathlib import Path
from celery_app import task_a, task_b

# --- Prepare log folder and file ---
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)  # Create 'logs' folder if missing
timestamp = time.strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"log_{timestamp}.json"

# --- Logger setup for console ---
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

def print_summary_table(results: dict, task_times: dict, statuses: dict):
    """
    Prints an ASCII table with task name, status, duration, and result.
    """
    # Column widths
    name_w = max(len("task"), *(len(k) for k in results)) + 2 if results else 8
    status_w = max(len("status"), 6) + 2
    time_w = max(len("time_s"), 6) + 2
    result_w = 60  # cap result text width

    def row(task, status, duration, result):
        result_str = str(result)
        if len(result_str) > result_w:
            result_str = result_str[:result_w - 3] + "..."
        return f"{task:<{name_w}}{status:<{status_w}}{duration:<{time_w}}{result_str}"

    header = f"{'task':<{name_w}}{'status':<{status_w}}{'time_s':<{time_w}}result"
    separator = "-" * (name_w + status_w + time_w + result_w)

    print("\n" + header)
    print(separator)
    for t in results:
        s = statuses.get(t, "unknown")
        d = f"{task_times.get(t, 0.0):.3f}"
        print(row(t, s, d, results[t]))

def main():
    overall_start = time.time()
    print()
    log_json("start", message="Dispatching tasks")
    print("\n")

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

    # Progress bar visualization
    with tqdm(total=total, desc="Processing", ncols=80) as pbar:
        completed = 0
        while completed < total:
            for name, result in list(tasks.items()):
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

                    # Keep progress bar tidy
                    #tqdm.write(f"{name} ({status}) → {output} [Time: {duration}s]")
                    #print("\n")

                    del tasks[name]
                    completed += 1
                    pbar.update(1)

            time.sleep(0.5)

    overall_end = time.time()

    # Print outputs in the original style
    #print(f"\nResult from task_a: {results.get('task_a')}")
    #print(f"Result from task_b: {results.get('task_b')}")


    # ASCII table summary
    print_summary_table(results, task_times, statuses)
    print("\n")

    # Calculate summary metrics
    success_rate = round((success_count / total) * 100, 2)

    # Log summary and total time
    total_time = round(overall_end - overall_start, 3)
    log_json("summary", total_tasks=total, success_rate=f"{success_rate}%")
    log_json("end", message="All tasks completed", total_time_s=total_time)


    print(f"\nLogs saved to: {log_file}\n")

if __name__ == "__main__":
    main()
