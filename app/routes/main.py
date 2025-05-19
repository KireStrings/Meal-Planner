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

@main.route('/planner', methods=['GET', 'POST'])
def planner():
    form = MealPlanForm()
    if form.validate_on_submit():
        # collect the form data
        calories = form.calories_per_day.data
        meals = form.num_meals.data
        price = form.avg_price.data
        diet = form.diet_type.data

        # Redirect to a result page or call your API handler
        return redirect(url_for('main.dashboard'))  # optional

    return render_template('planner.html', form=form)

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