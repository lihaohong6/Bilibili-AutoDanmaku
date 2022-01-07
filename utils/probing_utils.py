from pathlib import Path

from utils.config import log_flags
from utils.subprocess_utils import run_subprocess


def get_video_duration(file: Path) -> float:
    duration = run_subprocess(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                               "-of", "default=noprint_wrappers=1:nokey=1", file], capture_output=True, encoding='utf-8')
    return float(duration)


def get_video_codec(file: Path) -> str:
    codec = run_subprocess(["ffmpeg", "-loglevel error", "-select_streams", "v:0",
                            "-show_entries", "stream=codec_name", "-of",
                            "default=nk=1:nw=1", file])
    return codec
