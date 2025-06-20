from flask import Blueprint, current_app, request, render_template
from flask_login import login_required

from ..spoonacular import SpoonacularAPI

browse = Blueprint('browse', __name__)

@browse.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    recipes = []
    query = ''
    ingredients = ''
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)

    if request.method == 'POST':
        if 'query' in request.form:  # Search by query
            query = request.form.get('query')
            recipes = spoonacular.search_recipes(query).get('results', [])
        elif 'ingredients' in request.form:  # Search by ingredients
            ingredients = request.form.get('ingredients')
            recipes = spoonacular.search_recipes_with_ingredients(ingredients).get('results', [])

    return render_template('search.html', recipes=recipes, query=query, ingredients=ingredients)

@browse.route('/autocomplete', methods=['GET'])
@login_required
def autocomplete():
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)
    query = request.args.get('q', '')
    ingredients = spoonacular.autocomplete_ingredients(query)
    return {'results': ingredients}

@browse.route('/recipes')
@login_required
def recipes():
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)
    recipes = spoonacular.get_saved_recipes()
    return render_template('recipes.html', recipes=recipes)

@browse.route('/recipe/<int:recipe_id>')
@login_required
def recipe_details(recipe_id):
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)
    recipe_info = spoonacular.get_recipe_information(recipe_id)
    return render_template('recipe_details.html', recipe=recipe_info)