import requests

def check_queue(callback = None):
    response = requests.get("http://127.0.0.1:8188/queue")
    if response.status_code == 200:
        queue_data = response.json()
        queue_remaining = len(queue_data.get("queue_running", [])) + len(queue_data.get("queue_pending", []))
        print(f"Queue check: {queue_remaining} remaining")
        if queue_remaining == 0:
            if callback: callback()
    
    return queue_remaining