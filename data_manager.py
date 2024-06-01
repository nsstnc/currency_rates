from parser import Parser
from database import Database
from models import *
import pandas as pd
from functools import reduce

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

    def get_currencies(self, request_codes, sd, sm, sy, ed, em, ey):
        if len(request_codes) == 0:
            raise ValueError('Codes cannot be empty')

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
        # возвращаем только запрошенные валюты
        return result[['date'] + request_codes]
