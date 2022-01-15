import shutil
import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from utils.probing_utils import get_video_duration
from utils.subprocess_utils import run_subprocess

LAST_FRAME = Path(f"last.temp.png")


@dataclass
class Video:
    file: Path
    start_time: int
    duration: int
    trimmed_duration: int = -1


def get_epoch_millisecond(date_start, time_start, millis_start) -> int:
    """
    Convert strings representing a time to epoch time in milliseconds
    :param date_start: format "20211228"
    :param time_start: format "180520"
    :param millis_start: format "123"
    :return: an int representing epoch time in milliseconds.
    """
    time = datetime(year=int(date_start[0:4]), month=int(date_start[4:6]), day=int(date_start[6:8]),
                    hour=int(time_start[0:2]), minute=int(time_start[2:4]), second=int(time_start[4:6]),
                    microsecond=int(millis_start) * 1000)
    return round(time.timestamp() * 1000)


def create_freeze_frame(video: Video, output_file: Path, freeze_frame_time: int, temp_dir: Path):
    """
    Repeat the last frame of a video for a specified amount of time. Then return the
    generated video.
    :param temp_dir: temporary directory to store image file
    :param video: The video whose last frame will be repeated
    :param output_file: The path of the output video file
    :param freeze_frame_time: The duration of the new freeze frame video
    :return: A Video object representing the created video
    """
    last_frame = temp_dir.joinpath(LAST_FRAME)
    # extract the last frame of the video
    run_subprocess(["rm", "-f", last_frame])
    run_subprocess(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-sseof", "-1", "-i", video.file,
                    "-update", "1", "-q:v", "1", last_frame])
    # FIXME: copy codec of original video
    # repeat the last frame for a certain amount of time
    run_subprocess(["ffmpeg", "-hide_banner", "-loglevel", "warning",
                    "-loop", "1", "-i", last_frame, "-t", f"{freeze_frame_time / 1000}",
                    "-vcodec", "h264", "-vf", "format=yuv420p", "-acodec", "aac", "-r", "60",
                    output_file])

    return Video(output_file,
                 start_time=video.start_time + video.duration,
                 duration=freeze_frame_time)


def perform_smart_merge(videos: list[Video], temp_dir: Path):
    temp_videos: list[Video] = list()
    # process videos and see if they overlap or contain missing frames
    for index, curr in enumerate(videos[:-1]):
        after = videos[index + 1]
        overlap_time = curr.start_time + curr.duration - after.start_time
        if overlap_time < 0:
            # case 1: missing recording, so use frozen frame instead
            temp_videos.append(create_freeze_frame(curr,
                                                   temp_dir.joinpath(Path(f"temp{index}.flv")),
                                                   -overlap_time,
                                                   temp_dir))
        else:
            # case 2: recordings overlap; reduce the duration of the current video
            curr.trimmed_duration = curr.duration - overlap_time
    videos = videos + temp_videos
    return sorted(videos, key=lambda v: v.start_time)


def smart_merge(files: list[Path], temp_dir: Path, output: Path, smart: bool = True):
    durations: list[int] = [round(get_video_duration(f) * 1000) for f in files]
    videos: list[Video] = list()
    for index, file in enumerate(files):
        # extract video start time from file name
        if len(file.name.split("-")) < 6:
            print(f"File named {file.name} is not properly formatted. Ignoring.")
            continue
        # FIXME: is there a more accurate way to determine start time?
        start_time = get_epoch_millisecond(*file.name.split("-")[2:5])
        video = Video(file=file, start_time=start_time, duration=durations[index])
        videos.append(video)
    videos = sorted(videos, key=lambda v: v.start_time)
    if smart:
        videos = perform_smart_merge(videos, temp_dir)
    lines = []
    # format files in ffmpeg input file format
    for v in videos:
        lines.append(f"file '{v.file.absolute()}'")
        if v.trimmed_duration != -1:
            lines.append(f"duration {v.trimmed_duration / 1000}")
    with open(output, "w") as file:
        file.write("\n".join(lines))
        file.close()
