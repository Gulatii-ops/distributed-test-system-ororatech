"""
Simple dispatcher script that sends tasks concurrently and prints results.
"""

from celery_app import task_a, task_b

def main():
    print("Dispatching tasks...")

    # Run both tasks concurrently
    res_a = task_a.delay()
    res_b = task_b.delay()

    # Get results; the timeouts were added to avoid system hangs in case of an issue
    print(f"Result from task_a: {res_a.get(timeout=20)}")
    print(f"Result from task_b: {res_b.get(timeout=20)}")

if __name__ == "__main__":
    main()