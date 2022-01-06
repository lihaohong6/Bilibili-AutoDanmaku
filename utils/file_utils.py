import shutil
from pathlib import Path
from typing import Callable

TEMP_DIRECTORY = "./temp"


def assert_file_exists(file: Path):
    if not file.exists() or not file.is_file():
        print(f"File {file.name} does not exist")
        exit(1)


def execute_if_not_exist(file: Path, func: Callable):
    if not file.exists():
        func()
    assert_file_exists(file)


def create_temp_directory():
    """
    Create a directory to store temporary video files
    :return: None
    """
    p = Path(TEMP_DIRECTORY)
    if p.exists():
        if not p.is_file():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)
    p.mkdir(exist_ok=True)
    return p

