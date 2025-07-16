from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from ..spoonacular import SpoonacularAPI
import requests
import random
import os


# Define the blueprint for this page
dessert_drinks_page = Blueprint("dessert_drinks_page", __name__)

@dessert_drinks_page.route('/dessert_drinks_page', methods=['GET'])
@login_required
def dessert_view():
    return render_template('dessert_drinks_page.html')




def fetch_recipes(recipe_type, number, max_calories):
    api_key     = current_app.config['SPOONACULAR_API_KEY']
    spoon       = SpoonacularAPI(api_key)
    attempt_limit = 5
    recipes = []

    for _ in range(attempt_limit):
        offset = random.randint(0, 50)
        params = {
            "apiKey": api_key,
            "number": number,
            "addRecipeInformation": True,
            "addRecipeInstructions": False,
            "addRecipeNutrition": True,
            "type": recipe_type,
            "maxCalories": max_calories,
            "offset": offset,
            "sort": "popularity"
        }

        resp = spoon.search_recipes_by_params(params)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("results"):
                recipes.extend(data["results"])
                break

    return recipes[:number] if recipes else []

@dessert_drinks_page.route("/extras", methods=["POST"])
def get_extras():
    content = request.json
    selected_types = content.get("types", [])
    max_dessert = content.get("maxDessertCalories", 400)
    max_drink = content.get("maxDrinkCalories", 250)
    number = content.get("number", 2)

    result = {}

    if "dessert" in selected_types:
        result["dessert"] = fetch_recipes("dessert", number, max_dessert)

    if "drink" in selected_types:
        result["drink"] = fetch_recipes("drink", number, max_drink)

    return jsonify(result)