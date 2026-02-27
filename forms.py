from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Regexp, EqualTo

class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired(message="Please enter a username.")])
    password = PasswordField("Password:", validators=[InputRequired(message="Please enter a password.")])#Regexp('^(?=.*[a-z]+)(?=.*[A-Z])(?=.*[0-9])(?=.*[@!#?])[a-zA-Z0-9@!#?]{8,}$')
    password2 = PasswordField("Confirm Password:", validators=[EqualTo("password")])
    submit = SubmitField("Sign Up")

class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired(message="Please enter a username.")])
    password = PasswordField("Password:", validators=[InputRequired(message="Please enter a password.")])
    submit = SubmitField("Login")