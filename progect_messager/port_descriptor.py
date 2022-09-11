from asyncio.log import logger
import logging


logger = logging.getLogger('server_port_descriptor')


class Check_port:
    def __set__(self,instance,port):

        if (not 1023<port<65536) or (port%1 != 0):
            logger.critical(f'Порт:{port} задан не корректно. '
                              f'В качастве порта может быть указано только целое число в диапазоне от 1024 до 65535.')
            exit(1)
        instance.__dict__[self.my_attr] = port

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr
