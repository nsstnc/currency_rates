from parser import Parser
from database import Database
from models import *
import pandas as pd
from functools import reduce
from sqlalchemy import func, desc, asc, select, update
from typing import Type, Union
from sqlalchemy.orm import Query


class DataManager:
    def __init__(self):
        self.parser = Parser()
        self.session = self.init_db()
        self.add_default_date(datetime.date(2019, 5, 1))

    def init_db(self):
        db = Database('sqlite:///database.db')
        # создаем сессию
        session = db.create_session()
        return session

    def from_sql_to_dataframe(self, sql_data: Query) -> pd.DataFrame:
        # преобразуем результат в список словарей
        result = [row.__dict__ for row in sql_data]
        # удаляем внутренний атрибут SQLAlchemy '_sa_instance_state'
        for d in result:
            d.pop('_sa_instance_state', None)

        return pd.DataFrame(result)

    def add_default_date(self, date: datetime.date) -> None:
        existing_record = self.session.execute(select(Default_date).limit(1)).scalar_one_or_none()

        if existing_record is None:
            # если записей нет, добавляем новую запись
            self.session.add(Default_date(date=date))
            self.session.commit()
            self.get_currencies(["EUR"], date.day, date.month, date.year, date.day, date.month, date.year)

        else:
            if date != existing_record.date:
                self.session.execute(
                    update(Default_date)
                    .where(Default_date.id == existing_record.id)
                    .values(date=date)
                )
                self.session.commit()
                self.get_currencies(["EUR"], date.day, date.month, date.year, date.day, date.month, date.year)

    def get_default_date(self) -> datetime.date:
        return (self.session.execute(select(Default_date).limit(1)).scalar_one_or_none()).date

    def get_countries(self) -> pd.DataFrame:
        # парсим страны
        countries = self.parser.parse_countries()

        countries_from_db = self.from_sql_to_dataframe(self.session.query(Countries).order_by(
            asc(Countries.country)).all())

        # если в БД есть какие-то записи
        if not countries_from_db.empty:
            # изменившиеся и новые записи
            merged_df = countries.merge(countries_from_db, on='country', how='left', suffixes=('', '_existing'))

            changed_records = merged_df[
                (merged_df['code'] != merged_df['code_existing']) | merged_df['code_existing'].isna()]

            # выделяем только изменившиеся записи в новый фрейм
            changed_df = changed_records[['country', 'code']]

            for index, row in changed_df.iterrows():
                if pd.notna(row['code']):
                    # если запись существует, обновляем ее
                    self.session.query(Countries).filter(Countries.country == row['country']).update(
                        {'code': row['code']})
                    self.session.commit()
                else:
                    # если нет, добавляем новую
                    self.session.add([Countries(country=row['country'], code=row['code'])])
                    self.session.commit()
        else:
            # записываем страны в таблицу БД
            countries.to_sql('countries', con=self.session.bind, if_exists="append", index=False)
            self.session.commit()

        return self.from_sql_to_dataframe(self.session.query(Countries).order_by(
            asc(Countries.country)).all())

    # получаем минимальную и максимальную даты из БД в диапазоне date_start - date_end
    def get_existing_dates(self, date_start: datetime, date_end: datetime) -> (datetime.date, datetime.date, dict):
        existing_records = self.session.query(Rates).filter(Rates.date.between(date_start, date_end)).all()
        min_existing_date, max_existing_date = self.session.query(func.min(Rates.date), func.max(Rates.date)).filter(
            Rates.date.between(date_start, date_end)).one()

        return min_existing_date, max_existing_date, {record.date for record in existing_records}

    # получение курсов из базы данных
    def get_currencies_from_db(self, date_start: datetime, date_end: datetime,
                               table: Union[Type["Changes"], Type["Rates"]]) -> pd.DataFrame:
        result = self.from_sql_to_dataframe(
            self.session.query(table).filter(table.date.between(date_start, date_end)).order_by(
                asc(table.date)).all())

        return result

    def add_new_currencies_to_db(self, df: pd.DataFrame, existing_dates: dict) -> None:
        def calculate_relative_change(row, reference_row):
            return ((row - reference_row) / reference_row) * 100

        new_records = df[~df['date'].isin(existing_dates)]

        if not new_records.empty:
            # записываем новые значения в таблицу rates
            new_records.to_sql('rates', con=self.session.bind, if_exists="append", index=False)
            self.session.commit()

            reference_date = self.session.query(Default_date).one()
            reference_row_sql = self.session.query(Rates).filter(Rates.date == reference_date.date).first()
            reference_row = (pd.DataFrame(
                [{column.name: getattr(reference_row_sql, column.name) for column in
                  reference_row_sql.__table__.columns}])).iloc[0].drop(labels=['date', 'id'])

            # считаем относительные изменения курсов
            columns_to_calculate = new_records.columns.difference(['date'])
            relative_changes_df = new_records.copy()
            relative_changes_df[columns_to_calculate] = new_records[columns_to_calculate].apply(
                lambda row: calculate_relative_change(row, reference_row), axis=1)

            # добавляем относительные изменения курсов в таблицу changes
            relative_changes_df.to_sql('changes', con=self.session.bind, if_exists="append", index=False)
            self.session.commit()

    def get_currencies(self, request_codes: list, sd: int, sm: int, sy: int, ed: int, em: int, ey: int):
        if len(request_codes) == 0:
            raise ValueError('Не выбраны параметры')

        minimum_exist, maximum_exist, existing_dates = self.get_existing_dates(datetime.date(sy, sm, sd),
                                                                               datetime.date(ey, em, ed))

        # TODO когда даты старта или даты конца нет в бд, плохо отрабатывают третье и четвертое условия
        # если нижняя граница имеющихся курсов больше, чем требуемая дата
        # либо верхняя граница имеющихся ниже, чем требуемая
        if minimum_exist is None or maximum_exist is None or minimum_exist > datetime.date(sy, sm,
                                                                                           sd) or maximum_exist < datetime.date(
            ey, em, ed):
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
            # собираем в один датафрейм все курсы с привязкой к дате
            result = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
            # добавляем недостающие записи в БД
            self.add_new_currencies_to_db(result, existing_dates)

        print("берем из бд")
        table = self.get_currencies_from_db(datetime.date(sy, sm, sd), datetime.date(ey, em, ed), Rates)
        plot = self.get_currencies_from_db(datetime.date(sy, sm, sd), datetime.date(ey, em, ed), Changes)

        # возвращаем только запрошенные валюты
        return plot[['date'] + request_codes], table[['date'] + request_codes]
