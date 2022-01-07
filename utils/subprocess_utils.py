import subprocess
import traceback


def run_subprocess(args: list, **ops) -> str:
    for index in range(0, len(args)):
        if isinstance(args[index], float):
            args[index] = str(args[index])
    try:
        p: subprocess.CompletedProcess = subprocess.run(args, **ops)
        p.check_returncode()
        return str(p.stdout)
    except subprocess.CalledProcessError as e:
        print("===================Error Logs====================")
        print(args)
        print(e.output)
        traceback.print_exc()
        exit(1)