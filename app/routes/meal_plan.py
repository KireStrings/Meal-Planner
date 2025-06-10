from flask import Blueprint, render_template
from flask_login import current_user, login_required

meal_plan = Blueprint('meal_plan', __name__)

@meal_plan.route('/my-plan', methods=['GET'])
@login_required
def my_plan():
    return render_template('meal-plan.html', user=current_user)