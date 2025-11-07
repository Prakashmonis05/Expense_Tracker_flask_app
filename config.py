import os

class Config:
    SECRET_KEY = 'your_secret_key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234@localhost:5432/expense_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
