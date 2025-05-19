import requests

from .models import Recipe
from . import db
import json

class SpoonacularAPI:
    BASE_URL = "https://api.spoonacular.com"

    def __init__(self, api_key):
        self.api_key = api_key

    def search_recipes(self, query, number=10):
        """Suche nach Rezepten basierend auf einer Abfrage."""
        url = f"{self.BASE_URL}/recipes/complexSearch"
        params = {
            "query": query,
            "number": number,
            "apiKey": self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Fehler werfen, falls die Anfrage fehlschlägt
        return response.json()

    def search_recipes_with_ingredients(self, ingredients, number=10, sort="max-used-ingredients"):
        """
        Search for recipes using ingredients with additional filters.
        :param ingredients: A comma-separated list of ingredients.
        :param number: Number of recipes to return.
        :param sort: Sorting parameter (e.g., 'max-used-ingredients' or 'min-missing-ingredients').
        :return: JSON response with recipes.
        """
        url = f"{self.BASE_URL}/recipes/complexSearch"
        params = {
            "includeIngredients": ingredients,
            "number": number,
            "sort": sort,
            "apiKey": self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_recipe_information(self, recipe_id):
        """Hole detaillierte Informationen zu einem Rezept."""
        # Check if the recipe is already in the database
        recipe = Recipe.query.get(recipe_id)
        if recipe:
            return {
                "id": recipe.id,
                "title": recipe.title,
                "readyInMinutes": recipe.ready_in_minutes,
                "servings": recipe.servings,
                "summary": recipe.summary,
                "instructions": recipe.instructions,
                "extendedIngredients": json.loads(recipe.ingredients),
                "image": recipe.image_url,
                "source_name": recipe.source_name,
                "source_url": recipe.source_url
            }

        # If not, fetch from the API
        url = f"{self.BASE_URL}/recipes/{recipe_id}/information"
        params = {"apiKey": self.api_key}
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
            source_url=data.get("sourceUrl")  # Store the recipe URL
        )
        db.session.add(new_recipe)
        db.session.commit()

        return data