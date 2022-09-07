from task2 import host_range_ping
from tabulate import tabulate


def host_range_ping_tab():
    host_dict = host_range_ping(True)
    print(host_dict)
    print(tabulate([host_dict], headers='keys', tablefmt="pipe",stralign='center'))


if __name__ == "__main__":
    host_range_ping_tab()
