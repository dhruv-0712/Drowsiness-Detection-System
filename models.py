from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()
engine = create_engine("sqlite:///drowsiness.db", echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    active = Column(Boolean, default=True)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    type = Column(String)
    severity = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    extra = Column(Text)
    driver = relationship("Driver")

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    driver = relationship("Driver")

def init_db():
    Base.metadata.create_all(engine)
