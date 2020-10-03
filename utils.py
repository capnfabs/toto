# 'Dateutils' was already taken 😅
import datetime

from dateutil import tz

HOUR = datetime.timedelta(hours=1)
DAY = datetime.timedelta(days=1)
BERLIN_TIME = tz.gettz('Europe/Berlin')


def datetime_from_berlin_hhmmss(hour: int, min: int, sec: int) -> datetime.datetime:
    # TODO: check that this handles wrapping correctly
    now = datetime.datetime.now(tz=BERLIN_TIME)
    timestamp = now.replace(hour=hour, minute=min, second=sec,
                            microsecond=0)
    if timestamp > now:
        timestamp -= DAY
    return  timestamp
