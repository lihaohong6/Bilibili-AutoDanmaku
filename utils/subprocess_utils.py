import subprocess
import traceback


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