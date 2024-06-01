from bs4 import BeautifulSoup
import requests
import pandas as pd


class Parser:
    def __init__(self):
        self.currencies = {
            "USD": 52148,
            "EUR": 52170,
            "GBP": 52146,
            "JPY": 52246,
            "TRY": 52158,
            "INR": 52238,
            "CNY": 52207,
        }

    def parse_currency(self, currency_code, day_start, month_start, year_start, day_end, month_end, year_end):

        cur = self.currencies[currency_code]

        url = f"https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur={cur}&bd={day_start}&bm={month_start}&by={year_start}&ed={day_end}&em={month_end}&ey={year_end}"

        # получаем страницу с адреса, устанавливаем кодировку и создаем суп
        page = requests.get(url)
        page.encoding = 'windows-1251'
        soup = BeautifulSoup(page.text, "html.parser")
        # парсим таблицу
        table = soup.find("table", class_="karramba").find("tbody").find_all("td")
        # оставляем только содержимое тегов td
        for i in range(len(table)):
            table[i] = table[i].text

        # делим все полученные данные на разные строки
        data = [table[i:i + 4] for i in range(0, len(table), 4)]
        # записываем данные в датафрейм pandas
        df = pd.DataFrame(data, columns=['date', 'quantity', 'rate', 'change'])

        # приводим все столбцы к нужным типам
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')
        # df['quantity'] = df['quantity'].astype(int)
        df['rate'] = df['rate'].str.replace(',', '.').astype(float)
        # df['change'] = df['change'].str.replace('+', '').str.replace(',', '.').astype(float)

        return df[['date', 'rate']]

    def parse_countries(self):
        url = "https://www.iban.ru/currency-codes"

        # получаем страницу с адреса, устанавливаем кодировку и создаем суп
        page = requests.get(url)
        page.encoding = 'ISO 4217'
        soup = BeautifulSoup(page.text, "html.parser")

        # парсим таблицу
        table = soup.find("table", class_="table table-bordered downloads tablesorter").find("tbody").find_all("td")
        # оставляем только содержимое тегов td
        for i in range(len(table)):
            table[i] = table[i].text

        # делим все полученную таблицу на строки
        data = [table[i:i + 4] for i in range(0, len(table), 4)]
        # записываем данные в датафрейм pandas
        df = pd.DataFrame(data, columns=['country', 'currency', 'code', 'number'])

        df_filtered = df[df['code'].isin(set(self.currencies.keys()))]

        return df_filtered[['country', 'code']]
