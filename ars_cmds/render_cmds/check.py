import requests
from PyQt6.QtCore import QThread, pyqtSignal

# Keep references to active threads to prevent garbage collection
_active_threads = []

class QueueChecker(QThread):
    """Background thread for non-blocking queue checks."""
    finished = pyqtSignal(int)  # Emits queue_remaining count
        
    def run(self):
        try:
            response = requests.get("http://127.0.0.1:8188/queue", timeout=2)
            if response.status_code == 200:
                queue_data = response.json()
                queue_remaining = len(queue_data.get("queue_running", [])) + len(queue_data.get("queue_pending", []))
                # print(f"Queue check: {queue_remaining} remaining")
                self.finished.emit(queue_remaining)
            else:
                print(f"Queue check failed with status code: {response.status_code}")
                self.finished.emit(1)
        except requests.exceptions.RequestException as e:
            print(f"Error checking queue: {e}")
            self.finished.emit(1)


def check_queue_async(callback=None, on_empty=None):
    """
    Non-blocking queue check. Runs in a background thread.
    
    Args:
        callback: Called with queue_remaining count when check completes
        on_empty: Called (no args) only when queue is empty (0 remaining)
    """
    checker = QueueChecker()
    _active_threads.append(checker)
    
    def on_finished(queue_remaining):
        if callback:
            callback(queue_remaining)
        if queue_remaining == 0 and on_empty:
            on_empty()
        # Clean up thread reference
        if checker in _active_threads:
            _active_threads.remove(checker)
        checker.deleteLater()
    
    checker.finished.connect(on_finished)
    checker.start()
    return checker


# Keep synchronous version for cases where blocking is acceptable
def check_queue(callback=None):
    """Synchronous (blocking) queue check. Consider using check_queue_async instead."""
    try:
        response = requests.get("http://127.0.0.1:8188/queue", timeout=2)
        if response.status_code == 200:
            queue_data = response.json()
            queue_remaining = len(queue_data.get("queue_running", [])) + len(queue_data.get("queue_pending", []))
            # print(f"Queue check: {queue_remaining} remaining")
            if queue_remaining == 0:
                if callback: callback()
            return queue_remaining
        else:
            print(f"Queue check failed with status code: {response.status_code}")
            return 1
    except requests.exceptions.RequestException as e:
        print(f"Error checking queue: {e}")
        return 1