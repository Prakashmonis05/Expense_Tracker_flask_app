



from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Renamed to PascalCase for class names (Python convention)
class Account(UserMixin, db.Model):
    __tablename__ = 'account'  # maps to 'account' table in DB

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relationship with Expense table
    expenses = db.relationship('Expense', backref='account', lazy=True)


class Expense(db.Model):
    __tablename__ = 'expense'  # maps to 'expense' table in DB

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    type = db.Column(db.String(20), nullable=False)           # Income or Expense
    payment_mode = db.Column(db.String(20), nullable=False)   # Cash or Bank
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
