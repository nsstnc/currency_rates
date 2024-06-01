from parser import Parser
from database import Database
from models import *
import pandas as pd
from functools import reduce
from sqlalchemy import func, desc, asc

class DataManager:
    def __init__(self):
        self.parser = Parser()
        self.session = self.init_db()

    def init_db(self):
        db = Database('sqlite:///database.db')
        # создаем сессию
        session = db.create_session()
        # добавляем дефолтную дату для относительных изменений
        session.add(Default_date(date=datetime.date(2007, 10, 31)))
        session.commit()
        return session

    def get_countries(self):
        return self.parser.parse_countries()

    # получаем минимальную и максимальную даты из БД в диапазоне date_start - date_end
    def get_existing_dates(self, date_start: datetime, date_end: datetime):
        existing_records = self.session.query(Rates).filter(Rates.date.between(date_start, date_end)).all()
        min_existing_date, max_existing_date = self.session.query(func.min(Rates.date), func.max(Rates.date)).filter(
            Rates.date.between(date_start, date_end)).one()

        return min_existing_date, max_existing_date, {record.date for record in existing_records}

    # получение курсов из базы данных
    def get_currencies_from_db(self, date_start: datetime, date_end: datetime):
        result = self.session.query(Rates).filter(Rates.date.between(date_start, date_end)).order_by(asc(Rates.date)).all()
        # преобразуем результат в список словарей
        data = [row.__dict__ for row in result]
        # удаляем внутренний атрибут SQLAlchemy '_sa_instance_state'
        for d in data:
            d.pop('_sa_instance_state', None)

        return pd.DataFrame(data)

    def add_new_currencies_to_db(self, df, existing_dates):
        new_records = df[~df['date'].isin(existing_dates)]

        if not new_records.empty:
            new_records.to_sql('rates', con=self.session.bind, if_exists="append", index=False)

    def get_currencies(self, request_codes, sd, sm, sy, ed, em, ey):
        if len(request_codes) == 0:
            raise ValueError('Не выбраны параметры')


        minimum_exist, maximum_exist, existing_dates = self.get_existing_dates(datetime.date(sy, sm, sd),
                                                       datetime.date(ey, em, ed))


        # TODO когда даты старта или даты конца нет в бд, плохо отрабатывают третье и четвертое условия
        # если нижняя граница имеющихся курсов больше, чем требуемая дата
        # либо верхняя граница имеющихся ниже, чем требуемая
        if minimum_exist is None or maximum_exist is None or minimum_exist > datetime.date(sy, sm, sd) or maximum_exist < datetime.date(ey, em, ed):
            print("парсим")
            dfs = []
            # парсим курсы для всех валют в заданном диапазоне
            for code in ["USD",
                         "EUR",
                         "GBP",
                         "JPY",
                         "TRY",
                         "INR",
                         "CNY"]:
                df = self.parser.parse_currency(code, sd, sm, sy, ed, em, ey)
                df = df.rename(columns={'rate': f'{code}'})
                dfs.append(df)
            # собираем в один датафрейм все курсы с привязной к дате
            result = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
            # добавляем недостающие записи в БД
            self.add_new_currencies_to_db(result, existing_dates)
        else:
            print("берем из бд")
            result = self.get_currencies_from_db(datetime.date(sy, sm, sd), datetime.date(ey, em, ed))

        # возвращаем только запрошенные валюты
        return result[['date'] + request_codes]

