from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Expense
from config import Config
from datetime import datetime
import json

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')

def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
@app.route('/dashboard')
@login_required
def dashboard():
    # Calculate summary
    total_income = db.session.query(func.sum(Expense.amount))\
                     .filter_by(user_id=current_user.id, type='income').scalar() or 0
    total_expense = db.session.query(func.sum(Expense.amount))\
                      .filter_by(user_id=current_user.id, type='expense').scalar() or 0
    savings = total_income - total_expense

    # Category-wise expense data
    category_data = db.session.query(Expense.category, func.sum(Expense.amount))\
                     .filter_by(user_id=current_user.id, type='expense')\
                     .group_by(Expense.category).all()
    categories = [c[0] for c in category_data]
    category_values = [float(c[1]) for c in category_data]
    limit = request.args.get('limit', default=10, type=int)
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(limit).all()
    total_count = Expense.query.filter_by(user_id=current_user.id).count()
    # Monthly expense trend data
    expense_trend_data = db.session.query(
        func.strftime('%Y-%m', Expense.date).label('month'),
        func.sum(Expense.amount)
    ).filter_by(user_id=current_user.id, type='expense')\
     .group_by('month')\
     .order_by('month').all()
    
    # Monthly income trend data
    income_trend_data = db.session.query(
        func.strftime('%Y-%m', Expense.date).label('month'),
        func.sum(Expense.amount)
    ).filter_by(user_id=current_user.id, type='income')\
     .group_by('month')\
     .order_by('month').all()
    
    # Get all unique months from both income and expense
    all_months = sorted(set(
        [t[0] for t in expense_trend_data] + 
        [t[0] for t in income_trend_data]
    ))
    
    # Create dictionaries for easy lookup
    expense_dict = {t[0]: float(t[1]) for t in expense_trend_data}
    income_dict = {t[0]: float(t[1]) for t in income_trend_data}
    
    # Build aligned arrays
    months = all_months
    monthly_expenses = [expense_dict.get(month, 0) for month in all_months]
    monthly_income = [income_dict.get(month, 0) for month in all_months]
    monthly_savings = [monthly_income[i] - monthly_expenses[i] for i in range(len(all_months))]

    # Recent transactions
    expenses = Expense.query.filter_by(user_id=current_user.id)\
                      .order_by(Expense.date.desc()).all()

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expense=total_expense,
        savings=savings,
        categories=categories,
        category_values=category_values,
        months=months,
        monthly_expenses=monthly_expenses,
        monthly_income=monthly_income,
        monthly_savings=monthly_savings,
        expenses=expenses,total_count=total_count, limit=limit
    )

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        date = request.form['date']
        type = request.form['type']
        payment_mode = request.form['payment_mode']
        category = request.form['category']
        description = request.form['description']
        amount = float(request.form['amount'])

        new_entry = Expense(
            user_id=current_user.id,
            date=date,
            type=type,
            payment_mode=payment_mode,
            category=category,
            description=description,
            amount=amount
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add.html')


@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    try:
        expense = Expense.query.get_or_404(id)
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error deleting expense: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/transactions')
@login_required
def get_transactions():
    expenses = Expense.query.filter_by(user_id=current_user.id)\
                      .order_by(Expense.date.desc()).all()
    return jsonify([{
        'id': e.id,
        'date': e.date,
        'type': e.type,
        'category': e.category,
        'description': e.description,
        'amount': e.amount,
        'payment_mode': e.payment_mode
    } for e in expenses])


@app.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_transaction(id):
    expense = Expense.query.get_or_404(id)
    
    # ensure user owns this expense
    if expense.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json()

    # update fields safely
    expense.category = data.get('category', expense.category)
    expense.amount = float(data.get('amount', expense.amount))
    expense.date = data.get('date', expense.date)
    expense.description = data.get('description', expense.description)
    expense.payment_mode = data.get('payment_mode', expense.payment_mode)
    expense.type = data.get('type', expense.type)

    db.session.commit()
    return jsonify({'status': 'success'})



if __name__ == '__main__':
    app.run(debug=True)