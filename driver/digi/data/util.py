from datetime import datetime, timedelta, timezone


def now(no_zone=True):
    if no_zone:
        return datetime.now().replace(tzinfo=timezone(offset=timedelta()))
    else:
        return datetime.now()
