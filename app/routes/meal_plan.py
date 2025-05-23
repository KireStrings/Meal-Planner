from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

meal_plan = Blueprint('meal_plan', __name__)

@meal_plan.route('/my-plan', methods=['GET'])
def my_plan():
    return render_template('meal-plan.html', user=current_user)