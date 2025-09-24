"""
Celery application with two tasks and routing.
"""

import os
from celery import Celery

# Use localhost on Mac
BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@localhost:5672//")
# uses RabbitMQ (RPC) to return results
RESULT_BACKEND = os.getenv("RESULT_BACKEND", "rpc://")  

# Celery configuration setup
app = Celery("distributed-test-system")
app.conf.broker_url = BROKER_URL
app.conf.result_backend = RESULT_BACKEND
# Route each task to a specific queue
app.conf.task_routes = {
    "celery_app.task_a": {"queue": "queue_a"},
    "celery_app.task_b": {"queue": "queue_b"},
}

# Task implementation
@app.task(name="celery_app.task_a", bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def task_a(self):
    retry_count = self.request.retries
    # DEMO RETRY: Uncomment the lines below to demonstrate retry mechanism
    #if retry_count < 2:
    #    raise Exception(f"Simulated failure on attempt {retry_count + 1}")
    
    return {
        "result": "Hello from Task A",
        "retry_count": retry_count
    }

@app.task(name="celery_app.task_b", bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 3})
def task_b(self):
    retry_count = self.request.retries
    # DEMO RETRY: Uncomment the lines below to demonstrate retry mechanism
    if retry_count < 2:
        raise Exception(f"Simulated failure on attempt {retry_count + 1}")
    
    return {
        "result": "Hello from Task B",
        "retry_count": retry_count
    }
