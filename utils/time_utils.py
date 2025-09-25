import time

def get_current_epoch():
    return time.time()

def seconds_to_epoch(seconds):
    return time.time() + seconds