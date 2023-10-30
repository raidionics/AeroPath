import logging
import sys


def get_logger():
    return logging.getLogger(__name__)


def setup_logger():
    # clear log
    file_to_delete = open("log.txt", "w")
    file_to_delete.close()

    file_handler = logging.FileHandler(filename="log.txt")
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        handlers=handlers,
    )

    return get_logger()


def read_logs():
    sys.stdout.flush()
    with open("log.txt", "r") as f:
        return f.read()


def flush_logs():
    sys.stdout.flush()
    # clear log
    file_to_delete = open("log.txt", "w")
    file_to_delete.close()
