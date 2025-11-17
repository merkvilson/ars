from PyQt6.QtCore import QTimer

def after(ms, cmd):
    QTimer.singleShot(ms, cmd)


def delay(cmd):
    def wrapper(duration = 1000, *args, **kwargs):
        value = QTimer.singleShot(duration, lambda: cmd(*args, **kwargs))
        return value
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

"""