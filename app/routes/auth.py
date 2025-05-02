from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms import LoginForm, RegisterForm
from app.models import User
from app import db
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id  # or any login logic you use
            flash('Logged in successfully!')
            return redirect(url_for('main.dashboard'))  # adjust as needed
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            # login logic here
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
