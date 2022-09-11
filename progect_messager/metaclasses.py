import dis
from pprint import pprint


class ServerVerifier(type):
    def __init__(cls, clsname, bases_class, clsdict):
        # Атрибуты, используемые в функциях классов
        attrs = []      # получаем с помощью 'LOAD_ATTR'
        methods = []    # получаем с помощью 'LOAD_GLOBAL' + 'LOAD_METHOD'
        for metod in clsdict:
            try:
                # Возвращает итератор по инструкциям в предоставленной функции
                # , методе, строке исходного кода или объекте кода.
                ret = dis.get_instructions(clsdict[metod])
                # Если не метод, то получаем исключение (например порт)
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)
                    elif i.opname == 'LOAD_GLOBAL' or i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(i.argval)
        # pprint(attrs)
        # Если сокет не инициализировался константами SOCK_STREAM(TCP) AF_INET(IPv4), то используется не TCP протокол
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')

        # Если обнаружено использование недопустимого метода connect, вызываем исключение:
        if 'connect' in methods:
            raise TypeError(
                'Использование метода connect недопустимо в серверном классе')

        super().__init__(clsname, bases_class, clsdict)
