from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, DecimalField, TextAreaField
from wtforms.validators import InputRequired, Regexp, Length, EqualTo
from flask_wtf.file import FileField, FileAllowed, FileRequired

class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    submit = SubmitField("Log In")

class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[InputRequired(), Regexp('^[a-zA-Z0-9]{6,}$', message="Username must be alphanumeric."), Length(min=6, message="Username must be minimum 6 characters long.")])
    password = PasswordField("Password:", validators=[InputRequired()])
    password2 = PasswordField("Confirm Password:", validators=[EqualTo("password")])
    submit = SubmitField("Sign Up")

# https://flask-wtf.readthedocs.io/en/1.2.x/form/?highlight=filefield
class AddProductForm(FlaskForm):
    name = StringField("Name:", validators=[InputRequired()])
    price = DecimalField("Price:", validators=[InputRequired()])
    image = FileField("Upload Image:", validators=[FileRequired(), FileAllowed(["jpg","jpeg","png","webp"])])
    description = TextAreaField("Description:", description="Product description...")
    submit = SubmitField("Add Product")

class AddressForm(FlaskForm):
    street = StringField("Street:", validators=[InputRequired()])
    city = StringField("City:", validators=[InputRequired()])
    eircode = StringField("Eircode:", validators=[InputRequired()])
    submit = SubmitField("Place Order")