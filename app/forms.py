from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), DataRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), DataRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')