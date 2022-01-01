import re
import subprocess
import sys
import traceback
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, NewType

from utils.file_utils import TEMP_DIRECTORY, assert_file_exists, create_temp_directory

Time = NewType('Time', Union[str, int])
DANMAKU_OFFSET = -3
log_flags = ["-hide_banner", "-loglevel", "warning"]


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


def run_subprocess(args: list):
    for index in range(0, len(args)):
        if isinstance(args[index], float):
            args[index] = str(args[index])
    try:
        subprocess.run(args).check_returncode()
    except subprocess.CalledProcessError as e:
        print("===================Error Logs====================")
        print(args)
        print(e.output)
        traceback.print_exc()
        exit(1)


def clip_section(source: Path, out: Path,
                 interval: TimeInterval, danmaku: Path = None):
    time_start = interval.time_start
    duration = interval.duration
    if not danmaku:
        run_subprocess(["ffmpeg", *log_flags, "-ss", time_start, "-i", source, "-t", duration, "-c", "copy", out])
    else:
        temp_video = Path(f"{TEMP_DIRECTORY}/temp_clip.flv")
        temp_sub = Path(f"{TEMP_DIRECTORY}/temp_subs.ass")
        run_subprocess(["ffmpeg", *log_flags, "-ss", time_start, "-i", source, "-t", duration, "-c", "copy", temp_video])
        run_subprocess(["ffmpeg", *log_flags, "-itsoffset", -duration + DANMAKU_OFFSET, "-i", danmaku, "-c", "copy", temp_sub])
        run_subprocess(["ffmpeg", *log_flags, "-i", temp_video, "-vf", f"ass={temp_sub}", out])
    assert_file_exists(out)


def split_and_assemble(source: Path, out: Path, intervals: list[TimeInterval], danmaku: Path = None):
    if len(intervals) == 1:
        clip_section(source, out, intervals[0], danmaku)
        return
    temp_files = []
    for index, interval in enumerate(intervals):
        temp_file = Path(f"{TEMP_DIRECTORY}/part{index}.flv")
        clip_section(source, temp_file, interval, danmaku)
        temp_files.append(temp_file)
    part_list = Path(f"{TEMP_DIRECTORY}/part_list.txt")
    with open(part_list, "w") as f:
        parts = "\n".join([f"file '../{str(f)}'" for f in temp_files])
        f.write(parts)
    run_subprocess(["ffmpeg", *log_flags, "-f", "concat", "-safe", "0", "-i", part_list, "-c", "copy", out])


def main():
    parser = ArgumentParser()
    parser.add_argument("-i", dest="input", type=Path)
    parser.add_argument("-o", dest="output", type=Path)
    parser.add_argument("-ts", dest="time_start", type=str)
    parser.add_argument("-te", dest="time_end", type=str)
    parser.add_argument("-tf", dest="time_file", type=Path, default=None)
    parser.add_argument("-d", dest="danmaku_file", type=Path, default=None)
    args = parser.parse_args()
    create_temp_directory()
    if not args.time_file:
        split_and_assemble(args.input, args.output,
                           [TimeInterval(args.time_start, args.time_end)],
                           args.danmaku_file)
    else:
        intervals = []
        with open(args.time_file) as f:
            lines = f.read().split("\n")
            for line in lines:
                line = re.split("[- ]+", line)
                ts, te = line[0], line[1]
                intervals.append(TimeInterval(ts, te))
        split_and_assemble(args.input, args.output, intervals, args.danmaku_file)


if __name__ == "__main__":
    main()
