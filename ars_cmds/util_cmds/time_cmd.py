from PyQt6.QtCore import QTimer

# Keep references to timers to prevent garbage collection
_timers = set()

def after(ms, cmd):
    """
    Executes cmd after ms milliseconds.
    Keeps a reference to the timer to prevent garbage collection of the callback.
    """
    timer = QTimer()
    timer.setSingleShot(True)
    
    def on_timeout():
        try:
            cmd()
        finally:
            if timer in _timers:
                _timers.remove(timer)
            timer.deleteLater()

    timer.timeout.connect(on_timeout)
    _timers.add(timer)
    timer.start(ms)


def delay(cmd):
    def wrapper(duration = 1000, *args, **kwargs):
        after(duration, lambda: cmd(*args, **kwargs))
    return wrapper

"""

import random
@delay
def doit():
    msg(random.randint(0,100))

# Example usage: 
# doit(duration = 5000)
# Alternative

def doit():
    msg(random.randint(0,100))

delay(doit)(5000) usage with after:

# alternative usage: after(5000, doit)

#delay(msg)(2000,"hello world") #use with arguments

"""