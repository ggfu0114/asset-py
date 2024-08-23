from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine(<Connection string>)

Session = sessionmaker(bind=engine)

