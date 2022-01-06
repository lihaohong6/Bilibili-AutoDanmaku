import re


def time_to_int(t: str) -> float:
    segments = t.split(":")
    multiplier = 60 ** (len(segments) - 1)
    result = 0
    for s in segments:
        result += float(s) * multiplier
        multiplier /= 60
    return result


class TimeInterval:
    def __init__(self, time_start: str, time_end: str):
        self.time_start = time_to_int(time_start)
        self.time_end = time_to_int(time_end)
        self.duration = self.time_end - self.time_start


def parse_interval(line: str) -> TimeInterval:
    s = re.split("[- ]+", line)
    ts, te = s[0], s[1]
    return TimeInterval(ts, te)
