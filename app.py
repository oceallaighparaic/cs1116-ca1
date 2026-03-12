from flask import Flask, render_template

from flask_session import Session
from flask import session, g

from flask import redirect, url_for, request, abort
from werkzeug.security import generate_password_hash, check_password_hash

import database.database as database
import helpers
import forms

from typing import Final

#region CONFIG
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.teardown_appcontext(database.close_db)
Session(app)
#endregion

# for all routes:
# - pass title arg for base template

@app.route("/", methods=["GET","POST"])
def home_page() -> str:
    return render_template(
        "generic/home.html", 
        title="Home"
    )

#region AUTHENTICATION
# NOTES:
# g.user_id and g.user are set when the user is logged in, otherwise None

@app.before_request
def load_auth() -> None:
    g.user_id = session.get("user_id", None)
    g.user = session.get("username", None)

# https://flask.palletsprojects.com/en/stable/errorhandling/
@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", error=error), 403

@app.route("/login", methods=["GET","POST"], strict_slashes=False)
@helpers.logout_required
def login_page() -> str:
    form = forms.LoginForm()
    message: str = ""

    if form.validate_on_submit():
        db = database.get_db()

        attempt_username: Final[str] = form.username.data
        attempt_password: Final[str] = form.password.data
        query = db.execute("SELECT id, username, password FROM users WHERE username = ? ;", (attempt_username,)).fetchone()

        # !-- errors
        if not query: # if the user doesn't exist
            form.username.errors += ["Username not found."]
        elif not check_password_hash(query["password"], attempt_password): # if password is incorrect
            form.password.errors += ["Incorrect password."]
        
        # !-- login
        if not form.username.errors and not form.password.errors:
            session.clear()

            session["user_id"] = query["id"]
            session["username"] = query["username"]

            return redirect(url_for(request.args.get("next","home_page")))

    return render_template(
        "auth/login.html",
        title="Login",
        form=form,
        message=message
    )

@app.route("/logout", methods=["GET","POST"], strict_slashes=False)
def logout_page() -> str:
    session.clear()
    return redirect(url_for(request.args.get("next","home_page")))

@app.route("/register", methods=["GET","POST"], strict_slashes=False)
@helpers.logout_required
def register_page() -> str:
    form = forms.RegisterForm()

    if form.validate_on_submit():
        db = database.get_db()

        username: Final[str] = form.username.data
        password: Final[str] = form.password.data

        # !-- errors
        if db.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username.lower(),)).fetchone():
            form.username.errors += ["Username already taken."]

        # !-- register
        if not form.username.errors and not form.password.errors:
            db.execute("INSERT INTO users(username, password) VALUES(?,?)", (username, generate_password_hash(password)))
            db.commit()

            return redirect(url_for('login_page'))

    return render_template(
        "auth/register.html",
        title="Sign Up",
        form=form
    )
#endregion