import datetime
import streamlit as st
from functools import reduce
import pandas as pd
from parser import Parser
from database import Database
from models import *
from data_manager import DataManager


data = DataManager()

# получаем страны с кодами валют
countries = data.get_countries()

col1, col2, _, _, _, _ = st.columns(6)

with col1:
    if st.button("Plot 📈", key="plot"):
        st.session_state['action'] = 'plot'

with col2:
    if st.button("Table 📅", key="table"):
        st.session_state['action'] = 'table'

col1, col2 = st.columns(2)
with col1:
    st.subheader("Выберите диапазон дат")

    date_start = st.date_input("С", value=datetime.datetime.now().date(),
                               min_value=datetime.date(1992, 1, 1),
                               max_value=datetime.datetime.now().date(),
                               key="date_start")
    date_end = st.date_input("По", value=min(datetime.datetime.now().date(), st.session_state.date_start),
                             min_value=st.session_state.date_start,
                             max_value=min(st.session_state.date_start + datetime.timedelta(days=365 * 2),
                                           datetime.datetime.now().date()),
                             key="date_end")
with col2:
    st.subheader("Выберите страны")
    options = st.multiselect(
        "Страны",
        options=countries['country'])

sd = date_start.day
sm = date_start.month
sy = date_start.year

ed = date_end.day
em = date_end.month
ey = date_end.year

# получаем коды для выбранных стран
filtered_countries = countries[countries['country'].isin(options)]
# оставляем уникальные коды
codes = list(filtered_countries['code'].unique())

# dfs = []
# for code in codes:
#     df = data.get_currencies(code, sd, sm, sy, ed, em, ey)
#     df = df.rename(columns={'rate': f'{code}'})
#     dfs.append(df)

if 'action' in st.session_state:
    try:
        result = data.get_currencies(codes, sd, sm, sy, ed, em, ey)

        if st.session_state['action'] == 'plot':
            st.line_chart(result.set_index('date'))
        elif st.session_state['action'] == 'table':
            st.table(result)
    except Exception as e:
        st.write("Выберите параметры")
else:
    st.write("Выберите тип отображения")
