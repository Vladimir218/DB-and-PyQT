import os
from re import S
import signal
import subprocess
from time import sleep
import sys
from unicodedata import name

PYTHON_PATH = sys.executable
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_subprocess(file_with_args):
    sleep(0.2)

    file_full_path = f"{PYTHON_PATH} {BASE_PATH}/{file_with_args}"
    args = f'gnome-terminal {file_full_path}'
    return subprocess.Popen(args, shell=True, preexec_fn=os.setpgrp)

process = []

if __name__ == '__main__':
    while True:
        TEXT_FOR_INPUT = "Выберите действие: q - выход , s - запустить сервер, k - запустить клиенты x - закрыть все окна: "
        action = input(TEXT_FOR_INPUT)

        if action == "q":
            break
        elif action == "s":
            process.append(get_subprocess(" -- python3 server_start.py"))
        elif action == 'k':
            print('Убедитесь, что на сервере зарегистрировано необходимо количество клиентов с паролем 123456.')
            print('Первый запуск может быть достаточно долгим из-за генерации ключей!')
            clients_count = int(
                input('Введите количество тестовых клиентов для запуска: '))
            # Запускаем клиентов:
            for i in range(clients_count):
                process.append(get_subprocess(f' -- python3 client_start.py -n user{i+1} -p 123456'))
                sleep(1)
        elif action == "x":
            while process:
                victim = process.pop()
                os.killpg(os.getpgid(victim.pid), signal.SIGTERM)
