from flask import Flask, render_template, session, request, url_for, redirect
from flask_session import Session
import database
import forms
from typing import Final
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.teardown_appcontext(database.close_db)
Session(app)

@app.before_request
def validate_session() -> None:
    if not "user_id" in session:
        session["user_id"] = None

@app.route("/")
def home() -> str:
    return render_template("home.html", session=session)

@app.route("/signup", methods=["GET","POST"], strict_slashes=False)
def register() -> str:
    form = forms.RegisterForm()
    message = ""
    if form.validate_on_submit():
        db = database.get_db()

        username: Final[str] = form.username.data
        u_errors: list[str] = []
        if not re.search(r'^.{6,18}$', username): u_errors += ["be between 6 and 18 characters"]
        if not re.search(r'^[a-zA-Z0-9_]+$', username): u_errors += ["be alphanumeric"]
        if u_errors:
            form.username.errors += [f"""Username must 
                                    {", ".join(u_errors[:-1] if len(u_errors)>1 else u_errors)}{("",",")[len(u_errors)>2] + ("", " and " + u_errors[-1])[len(u_errors)>1]}."""
                                    ]
        if not form.username.errors:
            if db.execute("""SELECT * FROM users WHERE LOWER(username) = LOWER(?) ;""", (username,)).fetchone(): 
                form.username.errors += ["Username is already taken."]

        password: Final[str] = form.password.data
        pw_errors: list[str] = []
        if not re.search(r'^.{8,}$', password): pw_errors += ["be minimum 8 characters"]
        if not re.search(r'[A-Z]+', password): pw_errors += ["contain atleast one capital letter"]
        if not re.search(r'[0-9]+', password): pw_errors += ["contain atleast one number"]
        if not re.search(r'[!@#?]+', password): pw_errors += ["contain atleast one symbol"]
        if pw_errors:
            form.password.errors += [f"""Password must 
                                    {", ".join(pw_errors[:-1] if len(pw_errors)>1 else pw_errors)}{("",",")[len(pw_errors)>2] + ("", " and " + pw_errors[-1])[len(pw_errors)>1]}."""
                                    ]

        if not form.username.errors and not form.password.errors:
            db.execute("""INSERT INTO users(username, password, permission) VALUES (?,?,'USER') ;""",(username,generate_password_hash(password)))
            db.commit()
            
            message = f"Account {username} created."
            return redirect(url_for('login'))
    return render_template("register.html", form=form, message=message)

@app.route("/login", methods=["GET","POST"], strict_slashes=False)
def login() -> str:
    form = forms.LoginForm()
    message = ""
    if form.validate_on_submit():
        username: Final[str] = form.username.data
        password: Final[str] = form.password.data

        db = database.get_db()
        user_check: str = db.execute("""SELECT id, password FROM users WHERE username = ? ;""",(username,)).fetchone()
        if not user_check:
            form.submit.errors += ["Incorrect username."]
        elif not check_password_hash(user_check["password"], password):
            form.password.errors += ["Incorrect password."]
        else:
            session.clear()
            session["user_id"] = user_check["id"]
            session["username"] = username
            message = f"Logged in to {username}."

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
    return render_template("register.html", form=form, message=message)

@app.route("/logout/", methods=["GET","POST"])
def logout() -> str:
    if session["user_id"]:
        session.clear()
    return redirect(url_for('home'))

@app.route ("/store/<item>", methods=["GET"])
def store(item: str) -> str:
    return f"{item.title()}"