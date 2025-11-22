import os

class Config:
    SECRET_KEY = 'your_secret_key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'postgresql://neondb_owner:npg_A4lXSzJU7GxR@ep-little-frost-a4t0ihy2-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
