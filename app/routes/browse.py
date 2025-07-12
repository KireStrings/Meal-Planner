from flask import Blueprint, current_app, request, render_template
from flask_login import login_required, current_user
from .recipes import get_saved_recipes_for_user
from . import browse

from ..spoonacular import SpoonacularAPI

browse = Blueprint('browse', __name__)

@browse.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    recipes = []
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)

    if request.method == 'POST' or request.args.get('q'):
        query_params = {
            "query": request.form.get("query") or request.args.get('q'),
            "diet": request.form.get("diet") or None,
            "intolerances": request.form.get("intolerances") or None,
            "cuisine": request.form.get("cuisine") or None,
            "excludeIngredients": request.form.get("excludeIngredients") or None,
            "maxReadyTime": request.form.get("maxReadyTime") or None,
            "number": 10,
            "addRecipeInformation": True
        }
        recipes = spoonacular.search_recipes_by_params(query_params).json().get('results', [])

    return render_template('search.html', recipes=recipes, form_data=request.form)

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
    sort_by = request.args.get('sort', 'name')
    recipes = get_saved_recipes_for_user(current_user.id)

    if sort_by == 'recent':
        # sort by most recently saved
        recipes = sorted(recipes, key=lambda r: r['saved_at'], reverse=True)
    else:
        # Default: sort alphabetically by title
        recipes = sorted(recipes, key=lambda r: r['title'].lower())

    return render_template('recipes.html', recipes=recipes, sort_by=sort_by)

@browse.route('/recipe/<int:recipe_id>')
@login_required
def recipe_details(recipe_id):
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)
    recipe_info = spoonacular.get_recipe_information(recipe_id)
    print('recipe_info', recipe_info)
    return render_template('recipe_details.html', recipe=recipe_info)