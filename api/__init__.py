from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import configparser


config = configparser.ConfigParser()
config.read('config.ini')
engine = create_engine(config['ASSET_CONFIG']['DbConnectionString'])

Session = sessionmaker(bind=engine)

