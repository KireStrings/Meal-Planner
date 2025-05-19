from . import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    last_meal = db.Column(db.String(250))  # Optional: last planned meal


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    ready_in_minutes = db.Column(db.Integer, nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=True)  # Store as a JSON string
    image_url = db.Column(db.String(500), nullable=True)  # Store the image URL
    source_name = db.Column(db.String(255), nullable=True)  # Store the source name
    source_url = db.Column(db.String(500), nullable=True)  # Store the recipe source URL
