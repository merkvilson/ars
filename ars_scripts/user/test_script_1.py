from PyQt6.QtCore import QTimer

def delay(cmd):
    def wrapper(duration = 1000, *args, **kwargs):
        QTimer.singleShot(duration, lambda: cmd(*args, **kwargs))
    return wrapper
    
@delay    
def doit(text):
    msg(text)
# doit2 = delay(doit)
    
# delay(doit)(2000, text="hello world")
doit(5000, text="something new")