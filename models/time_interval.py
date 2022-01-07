import re
from typing import Union


def time_to_float(t: Union[str, float, int]) -> float:
    if isinstance(t, float) or isinstance(t, int):
        return float(t)
    segments = t.split(":")
    multiplier = 60 ** (len(segments) - 1)
    result = 0
    for s in segments:
        result += float(s) * multiplier
        multiplier /= 60
    return result


class TimeInterval:
    def __init__(self, time_start: Union[str, float, int], time_end: Union[str, float, int]):
        self.time_start = time_to_float(time_start)
        self.time_end = time_to_float(time_end)
        self.duration = self.time_end - self.time_start


def parse_interval(line: str) -> TimeInterval:
    s = re.split("[- ]+", line)
    ts, te = s[0], s[1]
    return TimeInterval(ts, te)
