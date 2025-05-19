from flask import Blueprint, render_template, request, current_app
from flask_login import login_required
from ..spoonacular import SpoonacularAPI

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET'])
@login_required
def dashboard_view():
    # Just render the page; no meal_plan here
    return render_template('dashboard.html')

@dashboard.route('/generate', methods=['POST'])
@login_required
def generate_meal_plan():
    if request.method == 'POST':
        data = request.get_json()

        diet = data.get('diet', '')
        calories = data.get('calories', 1800)
        meals = data.get('meals', 3)
        min_carbs = data.get('minCarbs', 90)
        min_fat = data.get('minFat', 40)
        min_protein = data.get('minProtein', 90)

        api_key = current_app.config['SPOONACULAR_API_KEY']
        spoonacular = SpoonacularAPI(api_key)

        params = {
            "apiKey": api_key,
            "number": meals,
            "addRecipeInformation": True,      # includes title, image, dish types, etc.
            "addRecipeInstructions": True,     # includes step-by-step instructions
            "addRecipeNutrition": True,        # includes nutrition facts
            "diet": "" if diet.lower() == "anything" else diet.lower(),
            "minCarbs": min_carbs,
            "minFat": min_fat,
            "minProtein": min_protein,
            "maxCalories": calories            # Optional but recommended for targeting
        }

        return spoonacular.search_recipes_by_params(params)
            

