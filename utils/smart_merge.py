import shutil
import subprocess
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TEMP_DIRECTORY = "./temp"
LAST_FRAME_NAME = f"{TEMP_DIRECTORY}/last.temp.jpg"


@dataclass
class Video:
    file_name: str
    start_time: int
    duration: int
    trimmed_duration: int = -1


def get_epoch_millisecond(date_start, time_start, millis_start) -> int:
    time = datetime(year=int(date_start[0:4]), month=int(date_start[4:6]), day=int(date_start[6:8]),
                    hour=int(time_start[0:2]), minute=int(time_start[2:4]), second=int(time_start[4:6]),
                    microsecond=int(millis_start) * 1000)
    return round(time.timestamp() * 1000)


def create_freeze_frame(video: Video, output_file_name: str, freeze_frame_time: int):
    try:
        subprocess.run(["rm", "-f", LAST_FRAME_NAME]).check_returncode()
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-sseof", "-1", "-i", f"{video.file_name}",
                        "-update", "1", "-q:v", "1", LAST_FRAME_NAME]).check_returncode()
        # FIXME: copy codec of original video
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning",
                        "-loop", "1", "-i", LAST_FRAME_NAME, "-t", f"{freeze_frame_time / 1000}",
                        "-vcodec", "h264", "-vf", "format=yuv420p", "-acodec", "aac", "-r", "60",
                        output_file_name]).check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.output)

    return Video(output_file_name,
                 start_time=video.start_time + video.duration,
                 duration=freeze_frame_time)


def create_temp_directory():
    p = Path(TEMP_DIRECTORY)
    if p.exists():
        if not p.is_file():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)
    p.mkdir(exist_ok=True)


def main():
    parser = ArgumentParser()
    parser.add_argument("-l", dest="file_list", type=str)
    parser.add_argument("-d", dest="durations", type=str)
    parser.add_argument("-f", dest="output_file_name", type=str)
    args = parser.parse_args()
    file_list: list[str] = args.file_list.split(sep="\n")
    durations: list[int] = [round(float(d) * 1000) for d in args.durations.split(sep=" ") if d.strip()]
    videos: list[Video] = list()
    for index, file in enumerate(file_list):
        start_time = get_epoch_millisecond(*file.split("-")[2:5])
        video = Video(file_name=file, start_time=start_time, duration=durations[index])
        videos.append(video)
    videos = sorted(videos, key=lambda v: v.start_time)
    temp_videos: list[Video] = list()
    create_temp_directory()
    for index, curr in enumerate(videos[:-1]):
        after = videos[index + 1]
        overlap_time = curr.start_time + curr.duration - after.start_time
        if overlap_time < 0:
            temp_videos.append(create_freeze_frame(curr, f"{TEMP_DIRECTORY}/temp{index}.flv", -overlap_time))
        else:
            curr.trimmed_duration = curr.duration - overlap_time
    videos = videos + temp_videos
    videos = sorted(videos, key=lambda v: v.start_time)
    lines = []
    for v in videos:
        lines.append(f"file '{v.file_name}'")
        if v.trimmed_duration != -1:
            lines.append(f"duration {v.trimmed_duration / 1000}")
    file = open(args.output_file_name, "w")
    file.write("\n".join(lines))
    file.close()


if __name__ == '__main__':
    main()
