import os

class Config:
    SECRET_KEY = 'your_secret_key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'postgresql://expense_db_kwzv_user:HHdViICo7yR23jSTDyfkXUlERQofP1PP@dpg-d46p1124d50c7390v350-a/expense_db_kwzv'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
