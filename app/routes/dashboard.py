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
    return render_template('dashboard.html')

def generate_recipe_hash(recipe):
    identifier = f"{recipe.get('id', '')}-{recipe.get('title', '')}"
    return hashlib.md5(identifier.encode()).hexdigest()

@dashboard.route('/generate', methods=['POST'])
@login_required
def generate_meal_plan():
    data        = request.get_json()
    diet        = data.get('diet', '')
    meals       = int(data.get('meals', 3))
    total_cal   = int(data.get('calories', 2000))
    min_carbs   = data.get('minCarbs', 0)
    min_fat     = data.get('minFat', 0)
    min_prot    = data.get('minProtein', 0)
    max_carbs   = data.get('maxCarbs', None)
    health_pref = data.get('healthPreference')
    api_key     = current_app.config['SPOONACULAR_API_KEY']
    spoon       = SpoonacularAPI(api_key)

    # Optional reset
    if data.get("forceNew"):
        session["used_recipe_hashes"] = []

    def get_split_ratios():
        if meals == 1:
            return {"meal1": total_cal}
        if meals == 2:
            half = total_cal // 2
            return {"meal1": half, "meal2": half}
        if meals == 3:
            per = int(total_cal * 0.3)
            return {"breakfast": per, "lunch": per, "dinner": per}
        if meals == 4:
            return {
                "breakfast": int(total_cal * 0.3),
                "lunch":     int(total_cal * 0.4),
                "snack1":    int(total_cal * 0.1),
                "dinner":    int(total_cal * 0.2)
            }
        if meals == 5:
            return {
                "breakfast": int(total_cal * 0.2),
                "lunch":     int(total_cal * 0.3),
                "snack1":    int(total_cal * 0.1),
                "snack2":    int(total_cal * 0.1),
                "dinner":    int(total_cal * 0.2)
            }
        return {}

    splits = get_split_ratios()

    batch_cache = {}
    def fetch_batch(meal_type, cal):
        if meal_type in batch_cache:
            return batch_cache[meal_type]

        def do_query(with_type):
            params = {
                "number": 50,
                "addRecipeInformation": True,
                "addRecipeNutrition": True,
                "diet": "" if diet.lower() == "anything" else diet.lower(),
                "minCalories": int(cal * 0.5),
                "maxCalories": int(cal * 1.3),
                "sort": "popularity",
                "offset": random.randint(0, 50)
            }
            if with_type and meal_type in ("breakfast", "lunch", "dinner", "snack"):
                params["type"] = meal_type
            if max_carbs is not None:
                params["maxCarbs"] = max_carbs

            resp = spoon.search_recipes_by_params(params)
            return resp.json().get("results", [])

        batch = do_query(with_type=True)
        if not batch:
            print(f"[Fallback] No results for '{meal_type}' with type filter. Retrying without type...")
            batch = do_query(with_type=False)

        random.shuffle(batch)
        batch_cache[meal_type] = batch

        if meal_type == "breakfast":
            print(f"Breakfast results (after shuffle): {[r.get('title') for r in batch]}")

        return batch

    def pick_from_batch(meal_type, apply_macros):
        batch = fetch_batch(meal_type, splits.get(meal_type, 0))
        best = None
        best_score = float('inf') if health_pref == "noPreference" else -1
        fallback = []
        used_hashes = set(session.get("used_recipe_hashes", []))

        for rec in batch:
            h = generate_recipe_hash(rec)
            if h in used_hashes:
                continue
            fallback.append(rec)
            score = rec.get("healthScore", 0)
            if apply_macros:
                nutrients = {n["name"]: n["amount"] for n in rec["nutrition"]["nutrients"]}
                prot_min = 28 if meal_type == "breakfast" else round(min_prot / meals)
                if nutrients.get("Protein", 0) < prot_min:
                    continue

            if health_pref == "veryHealthy" and score < (40 if meal_type == "breakfast" else 64):
                continue
            elif health_pref == "mediumHealthy" and not (26 <= score <= 50):
                continue

            
            if health_pref == "noPreference":
                if score < best_score:
                    best_score, best = score, rec
            else:
                if score > best_score:
                    best_score, best = score, rec

        choice = best or (random.choice(fallback) if fallback else None)
        if choice:
            used_hashes.add(generate_recipe_hash(choice))
            session["used_recipe_hashes"] = list(used_hashes)
            if len(session["used_recipe_hashes"]) > 300:
                session["used_recipe_hashes"] = session["used_recipe_hashes"][-150:]
            return choice
        return None

    meal_plan = {}
    for meal, cal in splits.items():
        apply_macros = meal in ("breakfast", "lunch", "dinner")
        rec = pick_from_batch(meal, apply_macros)
        if rec:
            rec = spoon.get_recipe_information(rec['id'])
            meal_plan[meal] = [rec]
        else:
            meal_plan[meal] = {"error": f"No suitable {meal} found."}
    print("meal_plan:", meal_plan)
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

        db.session.add(new_plan)

        added_recipe_ids = set()

        for meal_list in meal_plan_data.values():
            if isinstance(meal_list, list):
                for recipe_data in meal_list:
                    rid = recipe_data.get('id')
                    if not rid or rid in added_recipe_ids:
                        continue

                    recipe = Recipe.query.get(rid)
                    if not recipe:
                        recipe = Recipe(
                            id=rid,
                            title=recipe_data.get('title', ''),
                            image_url=recipe_data.get('image', ''),
                            source_url=recipe_data.get('sourceUrl', ''),
                            source_name=recipe_data.get('sourceName', ''),
                            summary=recipe_data.get('summary', ''),
                            instructions=data.get("instructions"),
                            ingredients=json.dumps(recipe_data.get('extendedIngredients', [])),
                            ready_in_minutes=recipe_data.get('readyInMinutes', 0),
                            servings=recipe_data.get('servings', 1),
                            diets=json.dumps(recipe_data.get('diets', '')),
                            calories=next(
                                (n['amount'] for n in recipe_data.get('nutrition', {}).get('nutrients', [])
                                if n.get('name') == 'Calories'), None
                            )
                        )
                        db.session.add(recipe)

                    new_plan.recipes.append(recipe)
                    added_recipe_ids.add(rid)

        current_user.meal_plans.append(new_plan)
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
        calories=next(
            (n['amount'] for n in data.get('nutrition', {}).get('nutrients', [])
            if n.get('name') == 'Calories'), None
            )

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
                servings=servings,
                calories=calories
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

@dashboard.route("/unsave_recipe", methods=["POST"])
@login_required
def unsave_recipe():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        recipe_id = data.get("id")
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400

        # Find the saved recipe link
        saved_recipe = UserSavedRecipe.query.filter_by(
            user_id=current_user.id,
            recipe_id=recipe_id
        ).first()

        if not saved_recipe:
            return jsonify({"message": "Recipe not found in saved recipes"}), 404

        # Remove the link
        db.session.delete(saved_recipe)
        db.session.commit()

        return jsonify({"message": "Recipe unsaved successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
