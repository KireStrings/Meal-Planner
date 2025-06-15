from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from ..models import Recipe, db, MealPlan
import requests
import random
import hashlib

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET'])
@login_required
def dashboard_view():
    # Just render the page; no meal_plan here
    return render_template('dashboard.html')

def generate_recipe_hash(recipe):
    identifier = f"{recipe.get('id', '')}-{recipe.get('title', '')}"
    return hashlib.md5(identifier.encode()).hexdigest()

@dashboard.route('/generate', methods=['POST'])
@login_required
def generate_meal_plan():
    if request.method == 'POST':
        data = request.get_json()

        diet = data.get('diet', '')
        meals = int(data.get('meals', 3))
        total_calories = int(data.get('calories', 2000))
        min_carbs = data.get('minCarbs', 0)
        min_fat = data.get('minFat', 0)
        min_protein = data.get('minProtein', 0)
        max_carbs = data.get('maxCarbs', None)
        health_pref = data.get("healthPreference")

        meal_plan = {}
        used_hashes = set(session.get("used_recipe_hashes", []))

        def get_split_ratios():
            if meals == 1:
                return {"meal1": total_calories}
            elif meals == 2:
                return {"meal1": total_calories // 2, "meal2": total_calories // 2}
            elif meals == 3:
                return {
                    "breakfast": int(total_calories * 0.3),
                    "lunch": int(total_calories * 0.3),
                    "dinner": int(total_calories * 0.3)
                }
            elif meals == 4:
                return {
                    "breakfast": int(total_calories * 0.3),
                    "lunch": int(total_calories * 0.3),
                    "snack1": int(total_calories * 0.1),
                    "dinner": int(total_calories * 0.2)
                }
            elif meals == 5:
                return {
                    "breakfast": int(total_calories * 0.3),
                    "lunch": int(total_calories * 0.2),
                    "snack1": int(total_calories * 0.1),
                    "snack2": int(total_calories * 0.1),
                    "dinner": int(total_calories * 0.2)
                }
            return {}

        def make_request(meal_type, cal, apply_macros):
            min_cal = int(cal * 0.5)
            max_cal = int(cal * 1.3)

            best_recipe = None
            fallback_candidates = []
            best_score = float('inf') if health_pref == "noPreference" else -1

            def build_params(offset=None):
                base_macros = {
                    "minCarbs": 20,
                    "minFat": 10,
                    "minProtein": 28
                } if meal_type == "breakfast" else {
                    "minCarbs": round(min_carbs / meals),
                    "minFat": round(min_fat / meals),
                    "minProtein": round(min_protein / meals)
                }

                base_offset = {"veryHealthy": 0, "mediumHealthy": 2, "noPreference": 1}.get(health_pref, 0)

                params = {
                    "apiKey": "09cecb76996e47ecab4383edff96eaa5",
                    "number": 5,
                    "addRecipeInformation": True,
                    "addRecipeInstructions": False,
                    "addRecipeNutrition": True,
                    "diet": "" if diet.lower() == "anything" else diet.lower(),
                    "minCalories": min_cal,
                    "maxCalories": max_cal,
                    "sort": "popularity",
                    "type": meal_type if meal_type in ["breakfast", "lunch", "dinner", "snack"] else None,
                    "offset": base_offset + random.randint(0, 50)
                }

                if max_carbs is not None:
                    params["maxCarbs"] = max_carbs

                return {k: v for k, v in params.items() if v is not None}, base_macros

            for attempt in range(5):
                params, base_macros = build_params()
                response = requests.get("https://api.spoonacular.com/recipes/complexSearch", params=params)
                print("Attempt", attempt + 1, "URL:", response.url)

                if response.status_code != 200:
                    continue

                results = response.json().get("results", [])
                random.shuffle(results)

                for recipe in results:
                    recipe_hash = generate_recipe_hash(recipe)
                    if recipe_hash in used_hashes:
                        fallback_candidates.append(recipe)
                        continue

                    health_score = recipe.get("healthScore", 0)
                    print("recipe:", recipe.get("title"), "health_Score:", health_score)

                    if apply_macros:
                        nutrients = {n["name"]: n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", [])}
                        if nutrients.get("Protein", 0) < base_macros["minProtein"]:
                            continue
                        if nutrients.get("Fat", 0) < base_macros["minFat"]:
                            continue
                        if nutrients.get("Carbohydrates", 0) < base_macros["minCarbs"]:
                            continue
                        if max_carbs is not None and nutrients.get("Carbohydrates", 0) > max_carbs:
                            continue

                    if health_pref == "veryHealthy":
                        if meal_type == "breakfast" and health_score < 45:
                            continue
                        elif health_score < 64:
                            continue
                    elif health_pref == "mediumHealthy" and not (26 <= health_score <= 50):
                        continue

                    fallback_candidates.append(recipe)

                    if health_pref == "noPreference":
                        if health_score < best_score:
                            best_score = health_score
                            best_recipe = recipe
                    else:
                        if health_score > best_score:
                            best_score = health_score
                            best_recipe = recipe

            if not best_recipe and fallback_candidates:
                best_recipe = random.choice(fallback_candidates)

            if best_recipe:
                best_hash = generate_recipe_hash(best_recipe)
                used_hashes.add(best_hash)
                session["used_recipe_hashes"] = list(used_hashes)
                return [best_recipe]

            return []

        split = get_split_ratios()

        for meal, cal in split.items():
            apply_macros = meal in ["breakfast", "lunch", "dinner"]
            recipes = make_request(meal, cal, apply_macros)
            if not recipes:
                meal_plan[meal] = {
                    "error": f"No suitable {meal} recipes found based on the selected health and macro preferences."
                }
            else:
                meal_plan[meal] = recipes

        print("Meal plan keys:", meal_plan.keys())
        
        return jsonify(meal_plan)

@dashboard.route('/save_plan', methods=['POST'])
@login_required
def save_meal_plan():
    data = request.get_json()
    meal_plan_data = data.get('mealPlan', {})
    plan_title = data.get('planTitle', f"{current_user.username}'s plan")
    
    if not meal_plan_data:
        return jsonify({'error': 'Meal plan data is missing'}), 400

    try:
        # You may wish to assign a main recipe here; otherwise set to None
        first_valid_recipe = None
        for recipes in meal_plan_data.values():
            if isinstance(recipes, list) and recipes:
                first_valid_recipe = recipes[0]
                break

        new_plan = MealPlan(
            title=plan_title,
            _input_date=datetime.utcnow())
        
        for day_recipes in meal_plan_data.values():
            for recipe_data in day_recipes:
                recipe = Recipe.query.get(recipe_data['id'])
                if recipe:
                    new_plan.recipes.append(recipe)

        current_user.meal_plans.append(new_plan)

        db.session.add(new_plan)
        db.session.flush()  # Ensure the MealPlan ID is available


        db.session.commit()
        return jsonify({'message': 'Meal plan saved successfully', 'mealPlanId': new_plan.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to save meal plan: {str(e)}'}), 500
