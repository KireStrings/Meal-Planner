from flask import Blueprint, render_template
from ..models import MealPlan
from flask_login import current_user, login_required

meal_plan = Blueprint('meal_plan', __name__)

@meal_plan.route('/my-plan', methods=['GET'])
@login_required
def my_plan():
    user_plans = current_user.meal_plans.order_by(MealPlan._input_date.desc()).all()
    return render_template('meal-plan.html', meal_plans=user_plans)
