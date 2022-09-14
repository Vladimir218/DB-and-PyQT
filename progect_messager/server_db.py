from curses import echo
from enum import unique
from common.variables import *
import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker


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

    def __init__(self):
        # Создаём движок базы данных
        # SERVER_DATABASE - sqlite:///server_base.db3
        # echo=False - отключает вывод на экран sql-запросов)
        # pool_recycle - по умолчанию соединение с БД через 8 часов простоя обрывается
        # Чтобы этого не случилось добавляем pool_recycle=7200 (переустановка
        #    соединения через каждые 2 часа)
        # connect_args={'check_same_thread': False}) для того, чтобы не возникало конфликта
        # при доступе к БД из разных потоков: потока класса Server и основного потока

        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200,
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

        # Создаём таблицы
        self.metadata.create_all(self.database_engine)

        # Создаём отображения
        # Связываем класс в ORM с таблицей
        mapper(self.AllUsers,users_table)
        mapper(self.ActiveUsers,active_users_table)
        mapper(self.LoginHistory,user_login_history)

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


# Отладка
if __name__ == '__main__':
    test_db = ServerStorage()
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
