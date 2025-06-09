from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DecimalField, SelectField
from wtforms.validators import InputRequired, DataRequired, NumberRange, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), DataRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

class AccountForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), DataRequired(), Email()])
    password = PasswordField('New Password', validators=[])
    submit = SubmitField('Save Changes')

class MealPlanForm(FlaskForm):
    calories_per_day = IntegerField('Calories per day', validators=[DataRequired(), NumberRange(min=500, max=10000)])
    num_meals = IntegerField('Number of meals', validators=[DataRequired(), NumberRange(min=2, max=6)])
    avg_price = DecimalField('Average price per meal ($)', validators=[DataRequired()])
    diet_type = SelectField('Diet type', choices=[('any', 'Any'), ('vegetarian', 'Vegetarian'), ('vegan', 'Vegan'), ('keto', 'Keto')])
    submit = SubmitField('Generate Plan')