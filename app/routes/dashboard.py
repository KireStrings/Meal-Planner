from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required, current_user
from ..models import Recipe, db, MealPlan, UserSavedRecipe
import random
import hashlib
from ..spoonacular import SpoonacularAPI
import pytz
import json

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
    api_key = current_app.config['SPOONACULAR_API_KEY']
    spoonacular = SpoonacularAPI(api_key)

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
                response = spoonacular.search_recipes_by_params(params)
                print("Attempt", attempt + 1, "URL:", response.url, "Status Code:", response.status_code)

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
    meal_plan_data = data.get('plan', {})
    plan_title = data.get('title', f"{current_user.username}'s plan")

    if not meal_plan_data:
        return jsonify({'error': 'Meal plan data is missing'}), 400

    try:
        new_plan = MealPlan(
            title=plan_title,
            _input_date=datetime.utcnow()
        )

        # Extract recipe IDs from nested meal data
        recipe_ids = []
        for meal_list in meal_plan_data.values():  # breakfast/lunch/dinner
            if isinstance(meal_list, list):
                for recipe in meal_list:
                    rid = recipe.get('id')
                    if rid:
                        recipe_ids.append(rid)

        # Attach valid recipes to the meal plan
        for rid in recipe_ids:
            recipe = Recipe.query.get(rid)
            if recipe:
                new_plan.recipes.append(recipe)

        current_user.meal_plans.append(new_plan)
        db.session.add(new_plan)
        db.session.commit()

        return jsonify({'message': 'Meal plan saved successfully', 'mealPlanId': new_plan.id}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving meal plan: {str(e)}")
        return jsonify({'error': f'Failed to save meal plan: {str(e)}'}), 500


@dashboard.route("/save_recipe", methods=["POST"])
@login_required
def save_recipe():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        recipe_id = data["id"]
        title = data["title"]
        image_url = data.get("image") or data.get("image_url")
        source_url = data.get("sourceUrl")
        source_name = data.get("sourceName", "")
        summary = data.get("summary", "")
        instructions = data.get("instructions", "")
        ingredients = data.get("ingredients", [])
        ready_in_minutes = data.get("readyInMinutes", 0)
        servings = data.get("servings", 1)

        # Ensure the recipe exists in the Recipe table
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            recipe = Recipe(
                id=recipe_id,
                title=title,
                image_url=image_url,
                source_url=source_url,
                source_name=source_name,
                summary=summary,
                instructions=instructions,
                ingredients=json.dumps(ingredients),
                ready_in_minutes=ready_in_minutes,
                servings=servings
            )
            db.session.add(recipe)

        # Check if the user already saved it
        existing_link = UserSavedRecipe.query.filter_by(
            user_id=current_user.id,
            recipe_id=recipe_id
        ).first()

        if existing_link:
            return jsonify({"message": "Recipe already saved"}), 409  # 409 Conflict

        # Save link between user and recipe
        link = UserSavedRecipe(
            user_id=current_user.id,
            recipe_id=recipe_id,
            saved_at=datetime.now(pytz.utc)
        )
        db.session.add(link)
        db.session.commit()

        return jsonify({"message": "Recipe saved successfully"}), 201  # 201 Created

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
