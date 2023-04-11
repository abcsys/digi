from datetime import datetime, timezone


def now(aware=True):
    if aware:
        return datetime.now().replace(tzinfo=timezone.utc)
    else:
        return datetime.now()

def min_time(aware=True):
    if aware:
        return datetime.min.replace(tzinfo=timezone.utc)
    else:
        return datetime.min
