from flask import Flask, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from flask_session import Session
from flask import session, g

import database.database as database

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
def home() -> str:
    return render_template(
        "generic/home.html", 
        title="Home"
    )