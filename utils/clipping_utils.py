from pathlib import Path

from utils.config import log_flags, DANMAKU_OFFSET
from models.time_interval import TimeInterval
from utils.file_utils import TEMP_DIRECTORY, assert_file_exists
from utils.subprocess_utils import run_subprocess


def create_clip(source: Path, out: Path, time_start: float, duration: float, fast_seek: bool = True,
                encoding: str = None):
    if not encoding:
        encoding_flags = ["-c", "copy"]
    else:
        encoding_flags = encoding.split(" ")
    if fast_seek:
        run_subprocess(["ffmpeg", *log_flags, "-ss", time_start, "-i", source, "-t", duration, *encoding_flags, out])
    else:
        run_subprocess(["ffmpeg", *log_flags, "-i", source, "-ss", time_start, "-t", duration, *encoding_flags, out])


def clip_section(source: Path, out: Path,
                 interval: TimeInterval, danmaku: Path = None, fast_seek: bool = True, encoding: str = None):
    time_start = interval.time_start
    duration = interval.duration
    if not danmaku:
        create_clip(source, out, time_start, duration, fast_seek, encoding)
    else:
        temp_video = Path(f"{TEMP_DIRECTORY}/temp_clip.flv")
        temp_sub = Path(f"{TEMP_DIRECTORY}/temp_subs.ass")
        create_clip(source, temp_video, time_start, duration, fast_seek, encoding)
        run_subprocess(
            ["ffmpeg", *log_flags, "-itsoffset", -duration + DANMAKU_OFFSET, "-i", danmaku, "-c", "copy", temp_sub])
        run_subprocess(["ffmpeg", *log_flags, "-i", temp_video, "-vf", f"ass={temp_sub}", out])
    assert_file_exists(out)


def assemble(files: list[Path], out: Path):
    part_list = Path(f"{TEMP_DIRECTORY}/part_list.txt")
    with open(part_list, "w") as f:
        parts = "\n".join([f"file '{str(f.resolve())}'" for f in files])
        f.write(parts)
    run_subprocess(["ffmpeg", *log_flags, "-f", "concat", "-safe", "0", "-i", part_list, "-c", "copy", out])
