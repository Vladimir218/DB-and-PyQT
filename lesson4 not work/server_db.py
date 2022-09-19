from curses import echo
from enum import unique
from common.variables import *
import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import configparser
import os.path
from pprint import pprint

# Класс - серверная база данных:
class ServerStorage:

    # Класс - отображение таблицы всех пользователей
    class AllUsers:
        def __init__(self, login):
            self.id = None
            self.login = login
            self.last_login = datetime.datetime.now()

    # Класс - отображение таблицы активных пользователей:

    class ActiveUsers:
        def __init__(self, user_id, ip_adress, port, time_in):
            self.id = None
            self.user = user_id
            self.time_in = time_in
            self.ip_adress = ip_adress
            self.port = port

    # Класс - отображение таблицы истории входов пользователей
    class LoginHistory:
        def __init__(self, id_user, time_in, ip_adress, port):
            self.id = None
            self.user = id_user
            self.time_in = time_in
            self.ip_adress = ip_adress
            self.port = port

    # Класс - отображение таблицы контактов пользователей
    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Класс отображение таблицы истории действий
    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0


    def __init__(self,path):
        # Создаём движок базы данных
        # SERVER_DATABASE - sqlite:///server_base.db3
        # echo=False - отключает вывод на экран sql-запросов)
        # pool_recycle - по умолчанию соединение с БД через 8 часов простоя обрывается
        # Чтобы этого не случилось добавляем pool_recycle=7200 (переустановка
        #    соединения через каждые 2 часа)
        # connect_args={'check_same_thread': False}) для того, чтобы не возникало конфликта
        # при доступе к БД из разных потоков: потока класса Server и основного потока

        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})


        # Создаём объект MetaData
        self.metadata = MetaData()

        # Создаем таблицу пользователей
        users_table = Table("Users", self.metadata,
                           Column("id", Integer, primary_key=True),
                           Column("login", String, unique=True),
                           Column("last_login", DateTime))

        # Создаем таблицу активных пользователей
        active_users_table = Table("Active_users", self.metadata,
                           Column("id", Integer, primary_key=True),
                           Column("user", ForeignKey("Users.id"), unique=True),
                           Column("ip_adress", String),
                           Column("port", Integer),
                           Column("time_in", DateTime))

        # Создаем таблицу истории подключения пользователей
        user_login_history = Table("Login_history", self.metadata,
                           Column("id", Integer, primary_key=True),
                           Column("user", ForeignKey("Users.id")),
                           Column("ip_adress", String),
                           Column("port", Integer),
                           Column("time_in", DateTime))

        # Создаём таблицу контактов пользователей
        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # Создаём таблицу истории пользователей
        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )


        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        # Связываем класс в ORM с таблицей
        mapper(self.AllUsers,users_table)
        mapper(self.ActiveUsers,active_users_table)
        mapper(self.LoginHistory,user_login_history)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

        #Функция выполняющаяся при входе пользователя, записывает в базу факт входа
    def user_login(self,user_name,ip_adress,port):
        print(user_name, ip_adress, port)
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        rez = self.session.query(self.AllUsers).filter_by(login=user_name)

        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
        # Если нет, то создаём нового пользователя
        else:
            # Создаём экземпляр класса self.AllUsers, через который передаём данные в таблицу
            user = self.AllUsers(user_name)
            self.session.add(user)
            # Коммит здесь нужен для того, чтобы создать нового пользователя,
            # id которого будет использовано для добавления в таблицу активных пользователей
            self.session.commit()

        # Cоздаем запись в таблицу активных пользователей о факте входа.
        # Создаём экземпляр класса self.ActiveUsers, через который передаём данные в таблицу
        new_active_user = self.ActiveUsers(user.id, ip_adress, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # Создаём экземпляр класса self.LoginHistory, через который передаём данные в таблицу
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_adress, port)
        self.session.add(history)

        # Сохраняем изменения
        self.session.commit()

        # Функция, фиксирующая отключение пользователя
    def user_logout(self, username):
        # Запрашиваем пользователя, что покидает нас
        # получаем запись из таблицы self.AllUsers
        user = self.session.query(self.AllUsers).filter_by(login=username).first()

        # Удаляем его из таблицы активных пользователей.
        # Удаляем запись из таблицы self.ActiveUsers
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        # Получаем ID отправителя и получателя
        print(sender)
        sender = self.session.query(self.AllUsers).filter_by(login=sender).first().id
        print(sender)

        recipient = self.session.query(self.AllUsers).filter_by(login=recipient).first().id
        print(recipient)
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        print(sender_row)
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    # Функция добавляет контакт для пользователя.
    def add_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    # Функция удаляет контакт из базы данных
    def remove_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.AllUsers).filter_by(login=user).first()
        contact = self.session.query(self.AllUsers).filter_by(login=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # Удаляем требуемое
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    # Функция возвращает список известных пользователей со временем последнего входа.
    def users_list(self):
        # Запрос строк таблицы пользователей.
        query = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_login)

        # Возвращаем список кортежей
        return query.all()

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        query = self.session.query(
            self.AllUsers.login,
            self.ActiveUsers.ip_adress,
            self.ActiveUsers.port,
            self.ActiveUsers.time_in
        ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()

    # Функция, возвращающая историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        # Запрашиваем историю входа
        query = self.session.query(self.AllUsers.login,
                                   self.LoginHistory.time_in,
                                   self.LoginHistory.ip_adress,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        # Если было указано имя пользователя, то фильтруем по этому имени
        if username:
            query = query.filter(self.AllUsers.login == username)
        # Возвращаем список кортежей
        return query.all()
 # Функция возвращает список контактов пользователя.
    def get_contacts(self, username):
        # Запрашиваем указанного пользователя
        user = self.session.query(self.AllUsers).filter_by(login=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(self.UsersContacts, self.AllUsers.loginame). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]

    # Функция возвращает количество переданных и полученных сообщений
    def message_history(self):
        query = self.session.query(
            self.AllUsers.login,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        # Возвращаем список кортежей
        return query.all()


# Отладка
if __name__ == '__main__':

    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")


    # Инициализация базы данных
    test_db = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    # Выполняем "подключение" пользователя
    test_db.user_login('test_client_1', '198.168.1.1', 8081)
    test_db.user_login('test_client_2', '198.168.1.2', 7771)

    # Выводим список кортежей - активных пользователей
    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_users_list())

    # Выполняем "отключение" пользователя
    test_db.user_logout('test_client_1')
    # И выводим список активных пользователей
    print(' ---- test_db.active_users_list() after logout test_client_1 ----')
    print(test_db.active_users_list())

    # Запрашиваем историю входов по пользователю
    print(' ---- test_db.login_history(test_client_1) ----')
    print(test_db.login_history('test_client_1'))

    # и выводим список известных пользователей
    print(' ---- test_db.users_list() ----')
    print(test_db.users_list())

    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    pprint(test_db.users_list())
    pprint(test_db.active_users_list())
    test_db.user_logout('McG2')
    pprint(test_db.login_history('re'))
    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test3')
    test_db.add_contact('test1', 'test6')
    test_db.remove_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    pprint(test_db.message_history())
