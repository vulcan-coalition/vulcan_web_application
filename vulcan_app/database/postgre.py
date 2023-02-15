from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, DateTime
from datetime import datetime
import pytz

Base = declarative_base()


def create_database(path="vulcan@localhost:5432/overlord"):
    SQLALCHEMY_DATABASE_URL = "postgresql://" + path
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, pool_size=128, max_overflow=32
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


class Postgres:
    def __init__(self, url):
        self.engine, self.session = create_database(url)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.session()


class TimeStamp(TypeDecorator):
    impl = DateTime
    LOCAL_TIMEZONE = datetime.utcnow().astimezone().tzinfo
    cache_ok = True

    def process_bind_param(self, value: datetime, dialect):
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)

        return value.astimezone(pytz.utc)

    def process_result_value(self, value, dialect):
        if value.tzinfo is None:
            return value.replace(tzinfo=pytz.utc)
