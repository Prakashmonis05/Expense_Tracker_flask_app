from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Expense
from config import Config
from datetime import datetime
import json
from datetime import datetime, timedelta

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
    user_id = current_user.id
    filter_option = request.args.get('filter', 'all')
    today = datetime.now().date()
    
    # Base query
    query = Expense.query.filter_by(user_id=user_id)
    
    # --- Date Filters ---
    if filter_option == 'today':
        query = query.filter(Expense.date == today)
    elif filter_option == '7days':
        start_date = today - timedelta(days=7)
        query = query.filter(Expense.date >= start_date)
    elif filter_option == '30days':
        start_date = today - timedelta(days=30)
        query = query.filter(Expense.date >= start_date)
    elif filter_option == 'thismonth':
        start_date = today.replace(day=1)
        query = query.filter(Expense.date >= start_date)
    elif filter_option == 'lastmonth':
        first_day_this_month = today.replace(day=1)
        last_month_end = first_day_this_month - timedelta(days=1)
        start_date = last_month_end.replace(day=1)
        query = query.filter(Expense.date.between(start_date, last_month_end))
    
    # Get filtered expenses
    expenses = query.order_by(Expense.date.desc()).all()
    
    # --- Last 30 Days Income and Expense ---
    thirty_days_ago = today - timedelta(days=30)
    
    last30_income = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.type == 'income',
        Expense.date >= thirty_days_ago
    ).scalar() or 0
    
    last30_expense = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.type == 'expense',
        Expense.date >= thirty_days_ago
    ).scalar() or 0
    
    # --- Category-wise expense data ---
    category_data = db.session.query(Expense.category, func.sum(Expense.amount))\
        .filter_by(user_id=user_id, type='expense')\
        .group_by(Expense.category).all()
    categories = [c[0] for c in category_data]
    category_values = [float(c[1]) for c in category_data]
    
    # --- Monthly trends ---
    expense_trend_data = db.session.query(
        func.strftime('%Y-%m', Expense.date).label('month'),
        func.sum(Expense.amount)
    ).filter_by(user_id=user_id, type='expense')\
     .group_by('month')\
     .order_by('month').all()
    
    income_trend_data = db.session.query(
        func.strftime('%Y-%m', Expense.date).label('month'),
        func.sum(Expense.amount)
    ).filter_by(user_id=user_id, type='income')\
     .group_by('month')\
     .order_by('month').all()
    
    # Get all unique months
    all_months = sorted(set(
        [t[0] for t in expense_trend_data] + 
        [t[0] for t in income_trend_data]
    ))
    
    expense_dict = {t[0]: float(t[1]) for t in expense_trend_data}
    income_dict = {t[0]: float(t[1]) for t in income_trend_data}
    
    months = all_months
    monthly_expenses = [expense_dict.get(month, 0) for month in all_months]
    monthly_income = [income_dict.get(month, 0) for month in all_months]
    monthly_savings = [monthly_income[i] - monthly_expenses[i] for i in range(len(all_months))]
    
    # --- Payment mode balances (all-time) ---
    cash_income = db.session.query(func.sum(Expense.amount)).filter_by(
        payment_mode='cash', type='income', user_id=user_id
    ).scalar() or 0
    
    cash_expense = db.session.query(func.sum(Expense.amount)).filter_by(
        payment_mode='cash', type='expense', user_id=user_id
    ).scalar() or 0
    
    cash_balance = cash_income - cash_expense
    
    bank_income = db.session.query(func.sum(Expense.amount)).filter_by(
        payment_mode='bank', type='income', user_id=user_id
    ).scalar() or 0
    
    bank_expense = db.session.query(func.sum(Expense.amount)).filter_by(
        payment_mode='bank', type='expense', user_id=user_id
    ).scalar() or 0
    
    bank_balance = bank_income - bank_expense
    total_balance = cash_balance + bank_balance
    
    return render_template(
        'dashboard.html',
        expenses=expenses,
        last30_income=last30_income,
        last30_expense=last30_expense,
        total_balance=total_balance,
        bank_balance=bank_balance,
        cash_balance=cash_balance,
        categories=categories,
        category_values=category_values,
        months=months,
        monthly_expenses=monthly_expenses,
        monthly_income=monthly_income,
        monthly_savings=monthly_savings,
        filter=filter_option
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
    # from waitress import serve
    # serve(app, host='0.0.0.0', port=5000)
    app.run(debug=True)