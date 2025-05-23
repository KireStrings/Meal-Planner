from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.forms import MealPlanForm
from ..spoonacular import SpoonacularAPI

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/my-plan', methods=['GET'])
def my_plan():
    return render_template('meal-plan.html', user=current_user)

@main.route('/search', methods=['GET', 'POST'])
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

@main.route('/recipe/<int:recipe_id>')
def recipe_details(recipe_id):
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)
    recipe_info = spoonacular.get_recipe_information(recipe_id)
    return render_template('recipe_details.html', recipe=recipe_info)