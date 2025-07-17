import json

import requests
from flask import jsonify
from flask_login import current_user
from sqlalchemy import func

from . import db
from .models import Recipe, Ingredient, UserSavedRecipe


class SpoonacularAPI:
    BASE_URL = "https://api.spoonacular.com"

    # Endpoint for searching recipes with complex parameters
    COMPLEX_SEARCH_URL = f"{BASE_URL}/recipes/complexSearch"

    # Endpoint for getting detailed recipe information
    # RECIPES_DETAILS_URL = f"{BASE_URL}/recipes/{recipe_id}/information"

    # Endpoint for autocomplete ingredients
    MAX_RESULTS = 10  # how many results to return total
    API_FETCH_THRESHOLD = 5  # how many DB results to trigger API call if not enough
    AUTOCOMPLETE_URL = f"{BASE_URL}/food/ingredients/autocomplete"

    def __init__(self, api_key):
        self.api_key = api_key

    def search_recipes_by_params(self, params):
        params['apiKey'] = self.api_key
        params["fillIngredients"] = True  # Include ingredient details in the response
        response = requests.get(self.COMPLEX_SEARCH_URL, params=params)

        print(params)

        #response = requests.get("https://api.spoonacular.com/recipes/complexSearch?apiKey=0132d061f6834c90a8086d0e4556364d&number=1&addRecipeInformation=true&addRecipeNutrition=true&addRecipeInstructions=true")

        if response.status_code == 200:
            # Cache ingredients from the recipe data
            self._cache_ingredients_from_recipes(response.json())

        return response

    def search_recipes(self, query, number=10):
        """Suche nach Rezepten basierend auf einer Abfrage."""
        params = {
            "query": query,
            "number": number,
            "fillIngredients": True,  # Include ingredient details in the response
            "apiKey": self.api_key
        }
        response = requests.get(self.COMPLEX_SEARCH_URL, params=params)
        response.raise_for_status()  # Fehler werfen, falls die Anfrage fehlschlägt

        # Cache ingredients from the recipe data
        self._cache_ingredients_from_recipes(response.json())

        return response.json()

    def search_recipes_with_ingredients(self, ingredients, number=10, sort="max-used-ingredients"):
        """
        Search for recipes using ingredients with additional filters.
        :param ingredients: A comma-separated list of ingredients.
        :param number: Number of recipes to return.
        :param sort: Sorting parameter (e.g., 'max-used-ingredients' or 'min-missing-ingredients').
        :return: JSON response with recipes.
        """
        params = {
            "includeIngredients": ingredients,
            "number": number,
            "sort": sort,
            "fillIngredients": True,  # Include ingredient details in the response
            "apiKey": self.api_key
        }
        response = requests.get(self.COMPLEX_SEARCH_URL, params=params)
        response.raise_for_status()

        # Cache ingredients from the recipe data
        self._cache_ingredients_from_recipes(response.json())

        return response.json()

    def get_saved_recipes(self, user_id):
        """
        Hole alle Rezepte, die der Benutzer gespeichert hat.
        :param user_id: The ID of the user whose saved recipes to retrieve.
        :return: List of saved recipes with their details.
        """
        # Get all Recipe objects that this user saved individually
        recipes = db.session.query(Recipe, UserSavedRecipe) \
                   .join(UserSavedRecipe, Recipe.id == UserSavedRecipe.recipe_id) \
                   .filter_by(user_id=user_id).all()

        return [
            {
                "id": recipe.id,
                "title": recipe.title,
                "readyInMinutes": recipe.ready_in_minutes,
                "servings": recipe.servings,
                "summary": recipe.summary,
                "instructions": recipe.instructions,
                "extendedIngredients": json.loads(recipe.ingredients),
                "image": recipe.image_url,
                "sourceName": recipe.source_name,
                "sourceUrl": recipe.source_url,
                "saved_at": userSavedRecipe.saved_at,
                "saved": True  # This is a saved recipe
            }
            for (recipe, userSavedRecipe) in recipes
        ]

    def get_recipe_information(self, recipe_id):
        """
        Hole detaillierte Informationen zu einem Rezept.
        :param recipe_id: The recipe ID.
        :return: JSON recipe information.
        """
        # Check if the recipe is already in the database
        recipe = Recipe.query.get(recipe_id)
        #Check if recipe is in user_saved_recipes
        if recipe:
            saved = recipe.id in map((lambda recipe: recipe['id']), self.get_saved_recipes(current_user.id))
            return {
                "id": recipe.id,
                "title": recipe.title,
                "readyInMinutes": recipe.ready_in_minutes,
                "servings": recipe.servings,
                "summary": recipe.summary,
                "instructions": recipe.instructions,
                "extendedIngredients": json.loads(recipe.ingredients),
                "image": recipe.image_url,
                "sourceName": recipe.source_name,
                "sourceUrl": recipe.source_url,
                'diets': json.loads(recipe.diets),
                "calories": recipe.calories,
                "saved": saved
            }

        # If not, fetch from the API
        url = f"{self.BASE_URL}/recipes/{recipe_id}/information"
        params = {
            "apiKey": self.api_key,
            "includeNutrition": "True"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Save the recipe to the database
        new_recipe = Recipe(
            id=data["id"],
            title=data["title"],
            ready_in_minutes=data["readyInMinutes"],
            servings=data["servings"],
            summary=data.get("summary"),
            instructions=data.get("instructions"),
            ingredients=json.dumps(data.get("extendedIngredients", [])),
            image_url=data.get("image"),
            source_name=data.get("sourceName"),  # Store the source name
            source_url=data.get("sourceUrl"),  # Store the recipe URL
            diets=json.dumps(data.get('diets')),
            calories=next(
                (n['amount'] for n in data.get('nutrition', {}).get('nutrients', [])
                if n.get('name') == 'Calories'), None
            )
        )
        db.session.add(new_recipe)
        db.session.commit()

        # Cache ingredients from the recipe data
        self._cache_ingredients_from_recipes([data])

        return data

    def autocomplete_ingredients(self, query):
        q = query.strip().lower()
        if not q:
            return jsonify([])

        # 1. Search local DB first
        # Search name-matching ingredients first
        name_matches = Ingredient.query \
            .filter(func.lower(Ingredient.name).like(f"%{q}%")) \
            .order_by(Ingredient.name) \
            .limit(self.MAX_RESULTS) \
            .all()

        # Collect names to avoid duplicates
        seen_names = {ingredient.name for ingredient in name_matches}

        results = [{"name": ingredient.name, "image": ingredient.image} for ingredient in name_matches]

        # If still under max, add meta-matching ingredients
        if len(results) < self.MAX_RESULTS:
            remaining = self.MAX_RESULTS - len(results)
            meta_matches = Ingredient.query \
                .filter(func.lower(Ingredient.meta).like(f"%{q}%")) \
                .filter(~Ingredient.name.in_(seen_names)) \
                .order_by(Ingredient.name) \
                .limit(remaining) \
                .all()

            results += [
                {"name": ing.name, "image": ing.image}
                for ing in meta_matches
            ]
            seen_names.update(ing.name for ing in meta_matches)

        # 2. If we have fewer than threshold, fetch from Spoonacular API
        if len(results) < self.API_FETCH_THRESHOLD:
            params = {
                "query": q,
                "number": self.MAX_RESULTS,
                "metaInformation": "true",  # Include meta information in the results
                "apiKey": self.api_key}
            response = requests.get(self.AUTOCOMPLETE_URL, params=params)
            if response.status_code == 200:
                api_results = response.json()

                # 3. Add API results to the list, avoiding duplicates
                for ingredient in api_results:
                    if not any(r['name'] == ingredient.get('extendedName', ingredient['name']).lower() for r in results):
                        results.append({
                            "name": ingredient.get('extendedName', ingredient['name']).lower(),
                            "image": ingredient.get('image'),
                        })

                # Cache new ingredients from API in DB
                self._cache_ingredients(api_results)

                # Trim to MAX_RESULTS
                results = results[:self.MAX_RESULTS]

        return results

    def _cache_ingredients_from_recipes(self, recipe_data):
        """
        Extracts ingredients from recipe data and caches them in the database.
        :param recipe_data: List of recipe dictionaries, each containing ingredient information.
            May also have the recipe-list nested under a 'results' key.
        :return: None
        """
        if 'results' in recipe_data:
            recipe_data = recipe_data["results"]

        ingredients = []

        for recipe in recipe_data:
            # From /findByIngredients or /recipes/complexSearch or ...
            if 'usedIngredients' in recipe:
                ingredients += recipe['usedIngredients']
            if 'missedIngredients' in recipe:
                ingredients += recipe['missedIngredients']

            # From /recipes/{id}/information
            if 'extendedIngredients' in recipe:
                ingredients += recipe['extendedIngredients']


        self._cache_ingredients(ingredients)

    def _cache_ingredients(self, api_results):
        """
        api_results: list of ingredient-dicts from `/ingredients/autocomplete` or `_cache_ingredients_from_recipe()`, e.g.:
        [
          { "id": 9003, "name": "apple", "image": "apple.jpg" },
          ...
        ]
        """
        for ingredient in api_results:
            # Check if the ingredient already exists in the database or is already added in this batch
            name = ingredient.get('extendedName', ingredient['name']).lower()
            existing = Ingredient.query.filter_by(name=name).first()
            if existing:
                # Merge meta fields (existing + new)
                try:
                    existing_meta = set(json.loads(existing.meta))
                except Exception:
                    existing_meta = set()
                merged_meta = sorted(existing_meta.union(ingredient.get('meta', {})))
                # Update the existing ingredient if it has new metadata
                existing.meta = json.dumps(merged_meta)
            else:
                # If it doesn't exist, create a new Ingredient object
                new_ingredient = Ingredient(
                    name=name, # Store the extendedNme or name in lowercase
                    meta=json.dumps(ingredient.get('meta', {})),  # Store additional metadata as JSON string
                    image=ingredient.get('image')
                )
                db.session.add(new_ingredient)

        db.session.commit()

