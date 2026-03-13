#region IMPORTS
# general flask
from flask import Flask, render_template

# sessions
from flask_session import Session
from flask import session, g

# authentication
from flask import redirect, url_for, request, abort
from werkzeug.security import generate_password_hash, check_password_hash

# file uploads (https://flask-wtf.readthedocs.io/en/1.2.x/form/?highlight=filefield)
import os
from werkzeug.utils import secure_filename
import uuid

# homegrown organic grassfed modules
import database.database as database
import helpers
import forms

# my pedantic typehinting
from typing import Final
#endregion

#region CONFIG
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/images/products/"
app.teardown_appcontext(database.close_db)
Session(app)
#endregion

# for all routes:
# - pass title arg for base template

@app.route("/", methods=["GET","POST"])
def home_page() -> str:
    db = database.get_db()
    query = db.execute("SELECT * FROM products LIMIT 10 ;")
    return render_template(
        "generic/home.html", 
        title="Home",
        products=query
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
    return render_template("generic/error.html", error=error), 403

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

            # set admin
            if db.execute("SELECT users.id FROM users JOIN permissions ON users.permission = permissions.id WHERE LOWER(permissions.name) = 'admin' AND users.id = ? ;",(session["user_id"],)).fetchone():
                session["is_admin"] = True
            return redirect(request.args.get("next") or url_for("home_page"))

    return render_template(
        "auth/login.html",
        title="Login",
        form=form,
        message=message
    )

@app.route("/logout", methods=["GET","POST"], strict_slashes=False)
def logout_page() -> str:
    session.clear()
    g.admin = False
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

#region STORE
@app.route("/store", methods=["GET","POST"], strict_slashes=False)
def search_page() -> str:
    search_term: Final[str] = request.args.get("search",None)
    if not search_term: return redirect(url_for('home_page'))

    db = database.get_db()
    query = db.execute("SELECT * FROM products WHERE name LIKE ?",(f"%{search_term}%",)).fetchall()

    return render_template(
        "store/search.html",
        title=f"Search For {search_term}",
        search=search_term,
        products=query
    )

@app.route("/add-product", methods=["GET","POST"], strict_slashes=False)
@helpers.admin_only
def add_product_page() -> str:
    form = forms.AddProductForm()

    if form.validate_on_submit():
        db = database.get_db()

        name: Final[str] = form.name.data
        price: Final[float] = form.price.data
        image = form.image.data
        description: Final[str] = form.description.data
        
        # !-- errors
        if db.execute("SELECT id FROM products WHERE LOWER(name) = ?", (name.lower(),)).fetchone():
            form.name.errors += ["Name already taken."]

        # !-- add product
        if not form.name.errors:
            # https://flask-wtf.readthedocs.io/en/1.2.x/form/?highlight=filefield
            filename: Final[str] = secure_filename(f"{uuid.uuid4()}.{image.filename.split('.')[-1]}")
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            db.execute("INSERT INTO products(name, price_cents, image, description) VALUES (?,?,?,?)", (name,int(price*100),filename,description))
            db.commit()
            
            return redirect(url_for('home_page'))

    return render_template(
        "store/addproduct.html",
        title="Add Products",
        form=form
    )

@app.errorhandler(404)
def not_found(error) -> str:
    return render_template("generic/error.html", error=error), 404

@app.route("/product/<int:p_id>", methods=["GET","POST"], strict_slashes=False)
def product_page(p_id: int) -> str:
    db = database.get_db()
    product = db.execute("SELECT * FROM products WHERE id = ? ;", (p_id,)).fetchone()

    # !-- errors
    if not product:
        abort(404)

    # !-- product page
    return render_template(
        "store/product.html",
        title=product["name"],
        product=product
    )

@app.route("/add-to-cart/<int:p_id>", methods=["GET","POST"], strict_slashes=False)
@helpers.login_required
def add_to_cart(p_id: int) -> str:
    # !-- initialize cart
    if "cart" not in session:
        session["cart"] = {}

    # !-- guard against invalid ids
    db = database.get_db()
    if not db.execute("SELECT id FROM products WHERE id = ? ;",(p_id,)).fetchone():
        abort(403)

    # !-- add to cart
    if not p_id in session["cart"]:
        session["cart"][p_id] = 0
    session["cart"][p_id] += 1

    return redirect(url_for('cart_page'))
    
@app.route("/cart/", methods=["GET","POST"], strict_slashes=False)
@helpers.login_required
def cart_page() -> str:
    # !-- intialize cart
    if "cart" not in session:
        session["cart"] = {}
    
    # !-- fetch names
    names: dict[int:str] = {}
    db = database.get_db()
    for p_id,_ in session["cart"].items():
        p = db.execute("SELECT name FROM products WHERE id = ? ;",(p_id,)).fetchone()
        names[p_id] = p["name"]

    return render_template(
        "store/cart.html",
        title="My Cart",
        cart=session["cart"],
        names=names
    )

@app.route("/remove-cart/<int:p_id>", methods=["GET","POST"], strict_slashes=False)
@helpers.login_required
def remove_from_cart(p_id: int) -> str:
    if p_id not in session["cart"]:
        return redirect(url_for('cart_page'))
    
    session["cart"][p_id] -= 1
    if session["cart"][p_id] <= 0:
        session["cart"].pop(p_id)
    return redirect(url_for('cart_page'))

@app.route("/remove-product/<int:p_id>", methods=["GET","POST"], strict_slashes=False)
@helpers.admin_only
def remove_product(p_id: int) -> str:
    db = database.get_db()

    if not db.execute("SELECT * FROM products WHERE id = ?", (p_id,)).fetchone():
        return redirect(url_for('home_page'))
    
    db.execute("DELETE FROM products WHERE id = ?", (p_id,))
    db.commit()

    return redirect(url_for('home_page'))
#endregion

#region ORDERS
@app.route("/place-order", methods=["GET","POST"], strict_slashes=False)
@helpers.login_required
def place_order() -> str:
    # !-- guard
    if "cart" not in session:
        return redirect(url_for('home_page'))
    
    # !-- fetch names, prices
    names: dict[int:str] = {} # id:name
    prices: list[int] = []
    db = database.get_db()
    for p_id,_ in session["cart"].items():
        p = db.execute("SELECT id, name, price_cents FROM products WHERE id = ? ;",(p_id,)).fetchone()
        names[p_id] = p["name"]
        prices += [int(p["price_cents"])*session["cart"][int(p["id"])]]

    total_price: int = sum(prices)

    # !-- place order
    form = forms.AddressForm()
    if form.validate_on_submit():
        street: str = form.street.data.strip(',')
        city: str = form.city.data.strip(',')
        eircode: str = form.eircode.data
        address: str = f"{street}, {city}, {eircode}"

        for p_id, quantity in session["cart"].items():
            # fetch price
            query: str = db.execute("SELECT price_cents FROM products WHERE id = ? ;", (p_id,)).fetchone()
            if not query: # guard for if somehow there is an incorrect id in the cart
                continue
            
            # create order
            db.execute("""
                INSERT INTO orders(userid, productid, quantity, price_at_purchase, address) 
                VALUES (?,?,?,?,?)
                ;""",
                (g.user_id, p_id, quantity, int(query["price_cents"]), address))
            db.commit()

        session["cart"] = {} # flush cart
        return redirect(url_for('orders_page'))  

    return render_template(
        "store/order.html",
        title="Finalize Order",
        form=form,
        names=names,
        price=total_price
    )

@app.route("/orders", methods=["GET","POST"], strict_slashes=False)
@helpers.login_required
def orders_page() -> str:
    db = database.get_db()
    query = db.execute("SELECT * FROM orders WHERE userid = ? ;",(g.user_id,)).fetchall()

    return render_template(
        "store/orders.html",
        title="Orders",
        query=query
    )

@app.route("/cancel-order/<int:o_id>", methods=["GET","POST"], strict_slashes=False)
@helpers.login_required
def cancel_order(o_id: int) -> str:
    db = database.get_db()
    
    # !-- guard
    order = db.execute("SELECT * FROM orders WHERE orderid = ? ;",(o_id,)).fetchone()
    if not order: # order doesnt exist
        return redirect(url_for('home_page'))
    if not order["userid"] == g.user_id: # user doesn't own order
        return redirect(url_for('orders_page'))

    # !-- cancel order
    db.execute("DELETE FROM orders WHERE orderid = ? ;",(o_id,))
    db.commit()

    return redirect(url_for('orders_page'))
#endregion