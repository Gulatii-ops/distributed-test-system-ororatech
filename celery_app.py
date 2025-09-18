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
@app.task(name="celery_app.task_a")
def task_a():
    return "Hello from Task A"

@app.task(name="celery_app.task_b")
def task_b():
    return "Hello from Task B"
