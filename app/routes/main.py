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

@main.route('/planner', methods=['GET', 'POST'])
def planner():
    form = MealPlanForm()
    if form.validate_on_submit():
        # collect the form data
        calories = form.calories_per_day.data
        meals = form.num_meals.data
        price = form.avg_price.data
        diet = form.diet_type.data

        # Redirect to a result page or call your API handler
        return redirect(url_for('main.dashboard'))  # optional

    return render_template('planner.html', form=form)