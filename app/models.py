from . import db
from flask_login import UserMixin
from datetime import datetime as dt, timezone as tz

user_mealplan = db.Table('user_mealplan',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('mealplan_id', db.Integer, db.ForeignKey('meal_plan.id'), primary_key=True)
)

mealplan_recipe = db.Table('mealplan_recipe',
    db.Column('mealplan_id', db.Integer, db.ForeignKey('meal_plan.id'), primary_key=True),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    last_meal = db.Column(db.String(250))  # Optional: last planned meal
    
    saved_recipes_assoc = db.relationship('UserSavedRecipe', backref='user', lazy='dynamic')

    meal_plans = db.relationship(
        'MealPlan',
        secondary='user_mealplan',
        backref=db.backref('users', lazy='dynamic'),
        lazy='dynamic'
    )

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    ready_in_minutes = db.Column(db.Integer, nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    calories = db.Column(db.Float)

    saved_by_assoc = db.relationship('UserSavedRecipe', backref='recipe', lazy='dynamic')

class UserSavedRecipe(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    saved_at = db.Column(db.DateTime, default=lambda: dt.now(tz.utc))

class MealPlan(db.Model):
    __tablename__ = 'meal_plan'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    _input_date = db.Column("input_date", db.DateTime)
    date = db.Column(db.String)
    recipes = db.relationship(
        'Recipe',
        secondary='mealplan_recipe',
        backref=db.backref('meal_plans', lazy='dynamic'),
        lazy='dynamic'
    )

    @property
    def input_date(self):
        return self._input_date
    
    @input_date.setter
    def input_date(self, value):
        self._input_date = value
        self.date = value.strftime("%A %d") if value else None

class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    name = db.Column(db.String, primary_key=True)
    image = db.Column(db.String, nullable=True)
    meta = db.Column(db.String, nullable=True)  # Store additional metadata as JSON string
    created_at = db.Column(db.DateTime, default=dt.utcnow)