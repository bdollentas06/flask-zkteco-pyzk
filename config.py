import os
from dotenv import load_dotenv

load_dotenv()

class ApplicationConfig:
    
    SQLALCHEMY_TRACK_MODIFICATION = False
    SECRET_KEY = os.getenv("JWT_SECRET")
    #Database
    SQLALCHEMY_DATABASE_URI = '{}://{}:{}@{}:{}/{}'.format(os.getenv("DB_CONNECTION"), os.getenv("DB_USERNAME"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT"), os.getenv("DB_DATABASE"))
    #Binds other Database
    SQLALCHEMY_BINDS = { 'nkti_adg': '{}://{}:{}@{}:{}/{}'.format(os.getenv("DB_CONNECTION"), os.getenv("ADG_DB_USERNAME"), os.getenv("ADG_DB_PASSWORD"), os.getenv("ADG_DB_HOST"), os.getenv("ADG_DB_PORT"), os.getenv("ADG_DB_DATABASE"))}