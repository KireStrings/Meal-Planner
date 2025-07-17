from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DecimalField, SelectField, EmailField
from wtforms.validators import InputRequired, DataRequired, NumberRange, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = EmailField('Email', validators=[InputRequired(), DataRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Register')

class AccountForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    email = EmailField('Email', validators=[InputRequired(), DataRequired(), Email()])
    password = PasswordField('New Password', validators=[])
    submit = SubmitField('Save Changes')