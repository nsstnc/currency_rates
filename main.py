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
    st.session_state['date_start'] = datetime.datetime.now().date() - datetime.timedelta(days=30)
    st.session_state['date_end'] = datetime.datetime.now().date()

    date_start = st.date_input("С",
                               min_value=datetime.date(1992, 1, 1),
                               max_value=datetime.datetime.now().date(),
                               key="date_start")
    date_end = st.date_input("По",
                             min_value=st.session_state["date_start"],
                             max_value=min(st.session_state["date_start"] + datetime.timedelta(days=365 * 2),
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



if 'action' in st.session_state:
    try:
        plot, table = data.get_currencies(codes, sd, sm, sy, ed, em, ey)
        if st.session_state['action'] == 'plot':
            st.write(f"Относительные изменения курсов валют к {data.get_default_date()}")
            st.line_chart(plot.set_index('date'))
        elif st.session_state['action'] == 'table':
            st.table(table)
    except Exception as e:
        st.write(e.args[0])
        # st.write(e)
else:
    st.write("Выберите тип отображения")
