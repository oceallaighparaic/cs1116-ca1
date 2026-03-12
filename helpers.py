from flask import g, redirect, url_for, request, abort
import functools
import database.database as database

def login_required(v):
    @functools.wraps(v)
    def wrapped_v(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login_page', next=request.url))
        return v(*args, **kwargs)
    return wrapped_v

def logout_required(v):
    @functools.wraps(v)
    def wrapped_v(*args, **kwargs):
        if g.user is not None:
            return redirect(url_for('home_page'))
        return v(*args, **kwargs)
    return wrapped_v

def admin_only(v):
    @functools.wraps(v)
    def wrapped_v(*args, **kwargs):
        db = database.get_db()
        user_perm: str = db.execute("""
            SELECT permissions.name AS user_perm
            FROM users
            JOIN permissions
            ON users.permission = permissions.id
            WHERE users.id = ? 
            ;""", 
        (g.user_id,)).fetchone()["user_perm"] # get user perm as a text name, not id
        if user_perm != "ADMIN":
            abort(403)
        return v(*args, **kwargs)
    return wrapped_v