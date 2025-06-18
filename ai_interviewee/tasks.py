from celery import shared_task
import time

@shared_task
def add(x, y):
    print(f"Executing add task with {x} and {y}")
    time.sleep(5) # Simulate a long-running task
    return x + y

@shared_task
def multiply(x, y):
    print(f"Executing multiply task with {x} and {y}")
    return x * y

@shared_task
def long_running_task():
    print("Starting long running task...")
    time.sleep(10) # Simulate a very long task
    print("Long running task finished.")
    return "Task completed!"
