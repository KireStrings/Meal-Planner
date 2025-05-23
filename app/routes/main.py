from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.forms import MealPlanForm

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/my-plan', methods=['GET'])
def my_plan():
    return render_template('meal-plan.html', user=current_user)