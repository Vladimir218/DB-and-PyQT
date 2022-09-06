from ipaddress import ip_address
from pickle import TRUE
import platform
from subprocess import Popen, PIPE
import os
import threading


SHARED_RESOURCE_LOCK = threading.Lock()


def check_is_ipadress(item):
    try:
        ipaddress = ip_address(item)
    except ValueError:
        raise Exception("введенные данные не являются ip адресом")
    return ipaddress


def url_ping(url):

    try:
        ipadress = check_is_ipadress(url)
    except Exception as er:
        ipadress = url

    param = "-n" if platform.system().lower() == 'windows' else "-c"
    command = ['ping', param, '1', '-w', '1', str(ipadress)]
    process = Popen(command, stdout=PIPE)

    if process.wait() == 0:
        with SHARED_RESOURCE_LOCK:
            res = f'{ipadress} - хост доступен'
    else:
        with SHARED_RESOURCE_LOCK:
            res = f'{ipadress} - хост недоступен'

    print(res)


if __name__ == "__main__":
    url_list = ('127.0.0.1', 'google.com',
                'onliner.by', 'yandex.ru', 'anyway.by', '8:8:8:8')
    print('Проверка доступности хостов')
    threads = []
    for host in url_list:
        t = threading.Thread(target=url_ping, args=(host,))
        threads.append(t)
        t.daemon = True
        t.start()

    for tr in threads:
        tr.join()
