import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI =  os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
