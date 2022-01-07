from argparse import ArgumentParser
from pathlib import Path

from models.time_interval import parse_interval
from utils.clipping_utils import clip_section, assemble
from utils.file_utils import create_temp_directory, TEMP_DIRECTORY


def main():
    parser = ArgumentParser()
    parser.add_argument("-i", dest="input", type=Path)
    parser.add_argument("-o", dest="output", type=Path)
    parser.add_argument("-tf", dest="time_file", type=Path)
    parser.add_argument("-safe", type=int, default=1)
    args = parser.parse_args()
    create_temp_directory()
    safe_mode = args.safe == 1
    with open(args.time_file, "r") as f:
        times = f.read().split("\n")
    with open(args.input, "r") as f:
        temp = f.read().split("\n")
        files: list[Path] = [Path(s) for s in temp]
    # FIXME: this could be more flexible
    assert len(files) == len(times)
    temp_files = []
    for index, f in enumerate(files):
        temp_file = Path(f"{TEMP_DIRECTORY}/temp{index}.mp4")
        if safe_mode:
            encoding = "-vcodec h264 -acodec copy"
        else:
            encoding = "-c copy"
        clip_section(f, temp_file, parse_interval(times[index]), fast_seek=not safe_mode, encoding=encoding)
        temp_files.append(temp_file)
    assemble(temp_files, args.output)


if __name__ == "__main__":
    main()
