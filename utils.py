# 'Dateutils' was already taken 😅
import datetime
from typing import Dict, Union

from dateutil import tz

HOUR = datetime.timedelta(hours=1)
MINUTE = datetime.timedelta(minutes=1)
DAY = datetime.timedelta(days=1)
BERLIN_TIME = tz.gettz('Europe/Berlin')

RequestParams = Dict[str, Union[str, int]]


def datetime_from_berlin_hhmmss(hour: int, min: int, sec: int) -> datetime.datetime:
    """Takes an hour / min / sec and contextualises it into a timestamp.
    Assumes that the hour / min / sec correspond to some time in the last 24
    hrs.
    """
    # TODO: check that this handles wrapping correctly
    now = datetime.datetime.now(tz=BERLIN_TIME)
    timestamp = now.replace(hour=hour, minute=min, second=sec,
                            microsecond=0)
    if timestamp > now:
        timestamp -= DAY
    return timestamp
