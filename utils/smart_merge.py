import shutil
import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from file_utils import TEMP_DIRECTORY, create_temp_directory

LAST_FRAME_NAME = f"{TEMP_DIRECTORY}/last.temp.jpg"


@dataclass
class Video:
    file_name: str
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


def create_freeze_frame(video: Video, output_file_name: str, freeze_frame_time: int):
    """
    Repeat the last frame of a video for a specified amount of time. Then return the
    generated video.
    :param video: The video whose last frame will be repeated
    :param output_file_name: The name of the output video file
    :param freeze_frame_time: The duration of the new freeze frame video
    :return: A Video object representing the created video
    """
    try:
        # extract the last frame of the video
        subprocess.run(["rm", "-f", LAST_FRAME_NAME]).check_returncode()
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-sseof", "-1", "-i", f"{video.file_name}",
                        "-update", "1", "-q:v", "1", LAST_FRAME_NAME]).check_returncode()
        # FIXME: copy codec of original video
        # repeat the last frame for a certain amount of time
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning",
                        "-loop", "1", "-i", LAST_FRAME_NAME, "-t", f"{freeze_frame_time / 1000}",
                        "-vcodec", "h264", "-vf", "format=yuv420p", "-acodec", "aac", "-r", "60",
                        output_file_name]).check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.output)
        exit(1)

    return Video(output_file_name,
                 start_time=video.start_time + video.duration,
                 duration=freeze_frame_time)


def main():
    parser = ArgumentParser()
    parser.add_argument("-l", dest="file_list", type=str,
                        help="A list of \\n separated flv file names from BililiveRecorder. "
                             "Use default file names because they contain date and time information.")
    parser.add_argument("-d", dest="durations", type=str,
                        help="A list of space separated number denoting the duration of each video in file list. ")
    parser.add_argument("-f", dest="output_file_name", type=str,
                        help="The name of the file to output. This file will later be used by ffmpeg to concat files.")
    args = parser.parse_args()
    file_list: list[str] = args.file_list.split(sep="\n")
    durations: list[int] = [round(float(d) * 1000) for d in args.durations.split(sep=" ") if d.strip()]
    videos: list[Video] = list()
    for index, file in enumerate(file_list):
        # extract video start time from file name
        # FIXME: is there a more accurate way to determine start time?
        start_time = get_epoch_millisecond(*file.split("-")[2:5])
        video = Video(file_name=file, start_time=start_time, duration=durations[index])
        videos.append(video)
    videos = sorted(videos, key=lambda v: v.start_time)
    temp_videos: list[Video] = list()
    create_temp_directory()
    # process videos and see if they overlap or contain missing frames
    for index, curr in enumerate(videos[:-1]):
        after = videos[index + 1]
        overlap_time = curr.start_time + curr.duration - after.start_time
        if overlap_time < 0:
            # case 1: missing recording, so use frozen frame instead
            temp_videos.append(create_freeze_frame(curr, f"{TEMP_DIRECTORY}/temp{index}.flv", -overlap_time))
        else:
            # case 2: recordings overlap; reduce the duration of the current video
            curr.trimmed_duration = curr.duration - overlap_time
    videos = videos + temp_videos
    videos = sorted(videos, key=lambda v: v.start_time)
    lines = []
    # format files in ffmpeg input file format
    for v in videos:
        lines.append(f"file '{v.file_name}'")
        if v.trimmed_duration != -1:
            lines.append(f"duration {v.trimmed_duration / 1000}")
    file = open(args.output_file_name, "w")
    file.write("\n".join(lines))
    file.close()


if __name__ == '__main__':
    main()
