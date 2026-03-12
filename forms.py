from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Regexp, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    submit = SubmitField("Log In")

class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired(), Regexp('^[a-zA-Z0-9]{6,}$', message="Username must be alphanumeric."), Length(min=6, message="Username must be minimum 6 characters long.")])
    password = PasswordField("Password:", validators=[InputRequired()])
    password2 = PasswordField("Confirm Password:", validators=[EqualTo("password")])
    submit = SubmitField("Sign Up")