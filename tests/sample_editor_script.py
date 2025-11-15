"""
Sample Python Code for Editor Demo

This script demonstrates various Python features including classes, decorators,
async functions, f-strings, and more. It simulates a simple task manager with
priority queue using heapq.

TODO: Add database integration
FIXME: Handle edge cases in task execution
"""

import heapq
import asyncio
import random
from typing import List, Dict, Callable
from functools import wraps

# Constants
PI = 3.14159
HEX_COLOR = 0xFF00FF
COMPLEX_NUM = 1 + 2j
LARGE_INT = 1_000_000_000_000

# Boolean and None
IS_ACTIVE = True
IS_DEBUG = False
EMPTY = None

def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Execution time for {func.__name__}: {end - start:.4f} seconds")
        return result
    return wrapper

class PriorityTask:
    """Class for tasks with priority."""

    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
        self._status = "pending"  # Private attribute
        self.__secret = "hidden"  # Name mangled

    def __str__(self) -> str:
        return f"Task({self.name}, priority={self.priority})"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, PriorityTask):
            return False
        return self.priority == other.priority and self.name == other.name

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        if value not in ["pending", "running", "done"]:
            raise ValueError("Invalid status")
        self._status = value

    async def execute(self):
        """Async method to simulate task execution."""
        print(f"Starting task: {self.name}")
        await asyncio.sleep(random.uniform(0.5, 2.0))
        print(f"Completed task: {self.name}")
        self.status = "done"

@timing_decorator
def process_tasks(tasks: List[PriorityTask]) -> Dict[str, str]:
    """Process tasks using a priority queue."""
    pq = []  # Priority queue as min-heap
    for task in tasks:
        heapq.heappush(pq, (task.priority, task))

    results = {}
    while pq:
        prio, task = heapq.heappop(pq)
        # Inline lambda
        transform = lambda x: x.upper() if IS_ACTIVE else x.lower()
        results[task.name] = transform(f"Processed with priority {prio}")

        # f-string with expressions and formatting
        msg = f"Task {task.name!r} (prio {prio:02d}) status: {task.status.upper()}"
        print(msg)

        # Raw string and byte string
        raw_path = r"C:\Users\Demo\file.txt"
        byte_data = b"Hello, world!"

        # Triple-quoted f-string with placeholder
        doc = f"""Multi-line f-string:
Value: {LARGE_INT:,}
Hex: {HEX_COLOR:#x}
Complex: {COMPLEX_NUM.imag}i
"""

        # Operators and braces
        total = (prio + 5) * 2 // 3 % 4 ** 2 & 0b1010 | 0o777 ^ 0xABC
        cond = prio > 0 and IS_DEBUG or not IS_ACTIVE
        shifted = prio << 2 >> 1

    return results

# Main execution
if __name__ == "__main__":
    # Class instantiation
    tasks = [
        PriorityTask("High priority", priority=-10),
        PriorityTask("Normal", priority=0),
        PriorityTask("Low priority", priority=10),
    ]

    # Function call
    results = process_tasks(tasks)

    # Async gathering
    async def run_all():
        await asyncio.gather(*(task.execute() for task in tasks))

    asyncio.run(run_all())

    # Dunder usage
    print(tasks[0] == tasks[1])
    print(repr(tasks[0]))

    # Builtin calls
    print(len(tasks))
    print(type(tasks))
    print(id(tasks[0]))

    # Lambda expression
    square = lambda x: x ** 2
    print(square(5))

    # Comment with NOTE
    # NOTE: End of demo script

    # Edge cases: unicode, escapes
    unicode_str = "Hello, 世界"
    escaped = "Line1\nLine2\tTabbed"
    f_escape = f"Value: {escaped!r}"

    # Dictionary comprehension with walrus
    data = {k: (v := random.randint(1, 10)) for k in range(5) if v > 5}
    print(data)