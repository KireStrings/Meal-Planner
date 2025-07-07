# app/saved_recipes.py
from flask import current_app
from ..spoonacular import SpoonacularAPI

def get_saved_recipes_for_user(user_id):
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)
    return spoonacular.get_saved_recipes(user_id)