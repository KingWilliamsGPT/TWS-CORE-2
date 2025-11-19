# tasks.py

from celery import Celery
import time

# Create a Celery instance
app = Celery('tasks', broker='redis://localhost:6379/0')

# Define the task
@app.task
def my_task(task_id):
    print(f"Task {task_id} started.")
    # Simulate some work
    time.sleep(5)
    print(f"Task {task_id} completed.")

# Define a function to schedule the tasks
def schedule_tasks():
    # Schedule 10 instances of the task
    for i in range(10):
        print("intiating task ...")
        my_task.apply_async(args=[i])

if __name__ == "__main__":
    print("starting tasks ...")
    schedule_tasks()
