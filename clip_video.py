from argparse import ArgumentParser
from pathlib import Path

from models.time_interval import TimeInterval, parse_interval
from utils.clipping_utils import clip_section, assemble
from utils.file_utils import TEMP_DIRECTORY, create_temp_directory


def split_and_assemble(source: Path, out: Path, intervals: list[TimeInterval], danmaku: Path = None):
    if len(intervals) == 1:
        clip_section(source, out, intervals[0], danmaku)
        return
    temp_files = []
    for index, interval in enumerate(intervals):
        temp_file = Path(f"{TEMP_DIRECTORY}/part{index}.flv")
        clip_section(source, temp_file, interval, danmaku)
        temp_files.append(temp_file)
    assemble(temp_files, out)


def main():
    parser = ArgumentParser()
    parser.add_argument("-i", dest="input", type=Path)
    parser.add_argument("-o", dest="output", type=Path)
    parser.add_argument("-t", dest="time_intervals", type=str, nargs="+", default=None)
    parser.add_argument("-ts", dest="time_start", type=str, nargs="+", default=[])
    parser.add_argument("-te", dest="time_end", type=str, nargs="+", default=[])
    parser.add_argument("-tf", dest="time_file", type=Path, default=None)
    parser.add_argument("-d", dest="danmaku_file", type=Path, default=None)
    args = parser.parse_args()
    create_temp_directory()
    intervals = []
    if not args.time_file:
        if args.time_intervals:
            for interval in args.time_intervals:
                intervals.append(parse_interval(interval))
        else:
            time_start = args.time_start
            time_end = args.time_end
            assert len(time_start) == len(time_end)
            for ts, te in zip(time_start, time_end):
                intervals.append(TimeInterval(ts, te))
    else:
        with open(args.time_file) as f:
            lines = f.read().split("\n")
            for line in lines:
                intervals.append(parse_interval(line))
    split_and_assemble(args.input, args.output, intervals, args.danmaku_file)


if __name__ == "__main__":
    main()
