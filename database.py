from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self._initialize_database()

    def _initialize_database(self):
        Base.metadata.create_all(self.engine)

    def create_session(self):
        return self.Session()
