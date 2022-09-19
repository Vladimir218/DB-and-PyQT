import os
import signal
import subprocess
from time import sleep
import sys

PYTHON_PATH = sys.executable
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_subprocess(file_with_args):
    sleep(0.2)

    file_full_path = f"{PYTHON_PATH} {BASE_PATH}/{file_with_args}"
    args = f'gnome-terminal {file_full_path}'
    return subprocess.Popen(args, shell=True, preexec_fn=os.setpgrp)

process = []
while True:
    TEXT_FOR_INPUT = "Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: "
    action = input(TEXT_FOR_INPUT)

    if action == "q":
        break
    elif action == "s":
        process.append(get_subprocess(" -- python3 server.py"))
        sleep(1)
        for i in range(2):
            process.append(get_subprocess(f' -- python3 client.py -n user{i+1}'))
            sleep(1)
    elif action == "x":
        while process:
            victim = process.pop()
            os.killpg(os.getpgid(victim.pid), signal.SIGTERM)
