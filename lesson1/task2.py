from posixpath import split
from task1 import check_is_ipadress, url_ping

def host_range_ping():
    while True:
        start_ip = input("Введите начальный IP адрес: ")

        try:
            ipadress = check_is_ipadress(start_ip)

            last_octet = int(str(ipadress).split(".")[3])

            break
        except Exception as e:
            print (f'Ошибка ввода')

    while True:
        quantity_ip_chek = input('Введите количество адресов для проверки: ')

        if not quantity_ip_chek.isnumeric():
            print("Введено не число")
        else:
            if int(quantity_ip_chek)-255>0:
                print(f'Число адресов для проверки должно быть менее {256- last_octet}')
            else:
                break


    ip_list = []

    [ip_list.append(str(ipadress+x)) for x in range(int(quantity_ip_chek))]

    for host in ip_list:
        url_ping(host)



if __name__ == "__main__":
    host_range_ping()
