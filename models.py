from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Date, Float
import datetime
Base = declarative_base()


# модель курса разных валют с привязкой к дате
class Rates(Base):
    __tablename__ = 'rates'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    USD = Column(Float)
    EUR = Column(Float)
    GBP = Column(Float)
    JPY = Column(Float)
    TRY = Column(Float)
    INR = Column(Float)
    CNY = Column(Float)


# модель стран с кодами валют в этих странах
class Countries(Base):
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True)
    country = Column(String)
    code = Column(String)


# модель изменения курсов валют относительно определенной даты
class Changes(Base):
    __tablename__ = 'changes'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    USD = Column(Float)
    EUR = Column(Float)
    GBP = Column(Float)
    JPY = Column(Float)
    TRY = Column(Float)
    INR = Column(Float)
    CNY = Column(Float)


# модель даты, от которой считаются относительные курсы
class Default_date(Base):
    __tablename__ = 'default_date'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
