from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import requests

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

        params = {
            "apiKey": "0132d061f6834c90a8086d0e4556364d",
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

        response = requests.get("https://api.spoonacular.com/recipes/complexSearch", params=params)

        print(params)
     
        #response = requests.get("https://api.spoonacular.com/recipes/complexSearch?apiKey=0132d061f6834c90a8086d0e4556364d&number=1&addRecipeInformation=true&addRecipeNutrition=true&addRecipeInstructions=true")


        if response.status_code == 200:
            print("API Response JSON:", response.json())
            return jsonify(response.json())
        else:
            print("error")
            return jsonify({"error": "Failed to fetch data"}), 500
            

