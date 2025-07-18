from flask import Blueprint, render_template, jsonify, current_app, request
from ..models import MealPlan
from flask_login import current_user, login_required
from ..models import db, MealPlan

meal_plan = Blueprint('meal_plan', __name__)

@meal_plan.route('/my-plan', methods=['GET'])
@login_required
def my_plan():
    user_plans = current_user.meal_plans.order_by(MealPlan._input_date.desc()).all()
    return render_template('meal-plan.html', meal_plans=user_plans)

@meal_plan.route('/unsave_plan/<int:plan_id>', methods=['DELETE'])
@login_required
def unsave_meal_plan(plan_id):
    try:
        # Find the meal plan by ID
        meal_plan = MealPlan.query.get(plan_id)

        if not meal_plan:
            return jsonify({'error': 'Meal plan not found'}), 404

        # Ensure the current user owns this plan
        if meal_plan not in current_user.meal_plans:
            return jsonify({'error': 'You do not have permission to delete this meal plan'}), 403

        # Remove the association between the user and the meal plan
        current_user.meal_plans.remove(meal_plan)

        # If no other users are associated, delete the plan and its recipe links
        if meal_plan.users.count() == 0:
            # Remove all recipe associations manually
            for recipe in meal_plan.recipes.all():
                meal_plan.recipes.remove(recipe)

            # Delete the meal plan itself
            db.session.delete(meal_plan)

        db.session.commit()
        return jsonify({'message': 'Meal plan unsaved successfully'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unsaving meal plan: {str(e)}")
        return jsonify({'error': f'Failed to unsave meal plan: {str(e)}'}), 500
    
@meal_plan.route('/rename_plan/<int:plan_id>', methods=['POST'])
@login_required
def rename_meal_plan(plan_id):
    try:
        # Find the meal plan by ID
        meal_plan = MealPlan.query.get(plan_id)

        if not meal_plan:
            return jsonify({'error': 'Meal plan not found'}), 404

        # Ensure the current user owns this plan
        if meal_plan not in current_user.meal_plans:
            return jsonify({'error': 'You do not have permission to rename this meal plan'}), 403

        # Get new title from request
        data = request.get_json()
        new_title = data.get('title', '').strip()

        if not new_title:
            return jsonify({'error': 'New title is required'}), 400

        # Update and commit
        meal_plan.title = new_title
        db.session.commit()

        return jsonify({'message': 'Meal plan renamed successfully', 'new_title': new_title}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error renaming meal plan: {str(e)}")
        return jsonify({'error': f'Failed to rename meal plan: {str(e)}'}), 500
