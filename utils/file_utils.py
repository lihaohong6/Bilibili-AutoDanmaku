import shutil
from pathlib import Path
from typing import Callable

TEMP_DIRECTORY = "./temp"


def assert_file_exists(file: Path):
    if not file.exists() or not file.is_file():
        print(f"File {file.name} does not exist")
        exit(1)


def execute_if_not_exist(file: Path, func: Callable, exit_if_fail: bool = False, **params) -> bool:
    if not file.exists():
        func(**params)
    if exit_if_fail:
        assert_file_exists(file)
        return True
    return file.exists() and file.is_file()


def create_temp_directory(p: Path = Path(TEMP_DIRECTORY)):
    """
    Create a directory to store temporary video files
    :return: None
    """
    if p.exists():
        if not p.is_file():
            shutil.rmtree(p)
        else:
            p.unlink(missing_ok=True)
    p.mkdir(exist_ok=True)
    return p

