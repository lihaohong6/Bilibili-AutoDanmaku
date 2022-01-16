import logging
import subprocess
import traceback


def run_subprocess(args: list, echo: bool = False, **ops) -> str:
    for index in range(0, len(args)):
        if isinstance(args[index], float) or isinstance(args[index], int):
            args[index] = str(args[index])
    if echo:
        logging.info(" ".join([str(a) for a in args]))
    try:
        p: subprocess.CompletedProcess = subprocess.run(args, **ops)
        p.check_returncode()
        return str(p.stdout)
    except subprocess.CalledProcessError as e:
        logging.error("===================Error Logs====================")
        logging.error(args)
        logging.error(e.output)
        logging.error("\n".join(traceback.format_exception(subprocess.CalledProcessError)))
        exit(1)