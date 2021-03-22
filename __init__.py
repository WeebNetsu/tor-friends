from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from collections import OrderedDict
from datetime import datetime

import json
import random

# my files
from auxillary import *

app = Flask(__name__)
test_env = True # if i'm using a test environment
    
with app.open_resource("static/src/json/config.json", 'r') as json_data:
    config_data = json.load(json_data)
    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqltype://username:password@host/database"
    if test_env:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tmp/users.db"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = config_data["database"]

app.url_map.strict_slashes = False  # doesn't force a "/" at the end of a link
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)  # link database and app


"""
from __init__ import db, Users

db.create_all()
"""
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.Text, nullable=False)
    mod_ = db.Column(db.Integer, nullable=False, default=0)  # 0 = false
    # admins are the only people who can remove mods
    admin_ = db.Column(db.Integer, nullable=False, default=0)
    # TODO: Do data signed in and torrent dates and stuffs
    date_accessed = db.Column(db.Date, nullable=False,
                              default=datetime.today().strftime('%Y-%m-%d'))

    # when you say BlogPost.query.all() the below will be returned
    def __repr__(self):
        return f"ID: {self.id}\nusername: {self.username}\npassword: {self.password}\nmod: {self.mod}"

# READING JSON FROM A FILE
try:
    json_data = app.open_resource("static/src/json/torrents.json", 'r')
    # will read from file (and convert to dictionary)
    torrents = OrderedDict(json.load(json_data))
    json_data.close()
except FileNotFoundError:
    # erase everything and rewrite the file
    tFile = app.open_resource("static/src/json/torrents.json", 'r')
    tFile.write("{\n}")
    tFile.close()

    json_data = app.open_resource("static/src/json/torrents.json", 'r')
    # will read from file (and convert to dictionary)
    torrents = OrderedDict(json.load(json_data))
    json_data.close()


def guest_sign_in():
    session["id"] = random.randint(1, 999999)  # guest random ID
    session["username"] = "Guest"
    session["guest"] = True
    flash("Signed in as Guest user", "info")

@app.route("/ads.txt")
def ads(): # so ads.txt can be accessed by ad website
	return send_from_directory("static", "ads.txt")

# NOTE: all render_templates should include session EXCEPT for login
@app.route("/rules/")
def rules():
    if not "id" in session:
        guest_sign_in()

    return render_template("rules.html", session=[session])


@app.route("/admin/user/mod/<string:category>/")
def edit_user_details(category):
    if "id" in session and "mod" in session and not "guest" in session:
        if request.args.get('wrongpass'):
            flash("Password is incorrect.", "error")

        if request.args.get('notfound'):
            flash("User not found. No changes made.", "error")

        if request.args.get('ismod'):
            flash("You cannot modify other mod details.", "warning")

        if request.args.get('usernameexist'):
            flash("Username already exist.", "error")

        if request.args.get('modded'):
            flash("Successfully made changes.", "info")

        return render_template("admin_mod_user.html", session=[session], category=category)

    return redirect(url_for("index", notmod=True))


@app.route("/admin/mod/user/set/<string:category>", methods=["GET", "POST"])
def set_user_details(category):
    if "id" in session and "mod" in session and not "guest" in session:
        if request.method == "POST":
            admin_password = request.form["admin_password"]

            admin = Users.query.filter_by(
                username=session["username"]).all()[0]
            if admin.password != encrypt_string(admin_password):
                return redirect(f"/admin/user/mod/{category}?wrongpass=True")

            username = request.form["username"]
            try:
                user = Users.query.filter_by(username=username).all()[0]
            except IndexError:  # if user not found
                return redirect(f"/admin/user/mod/{category}?notfound=True")
            else:
                if category == "username":
                    new_username = request.form["new_username"]
                    try:
                        _ = Users.query.filter_by(
                            username=new_username).all()[0]
                    except IndexError:  # if the username doesn't already exist
                        if user.mod_:
                            if not admin.admin_:
                                return redirect(f"/admin/user/mod/{category}?ismod=True")

                        # we already know the user exists, so no "or_404" needed
                        user = Users.query.get(user.id)
                        user.username = new_username
                        db.session.commit()

                        for key, val in torrents.items():
                            if(val["user"] == username):
                                val['user'] = new_username

                        write_torrent_json(torrents, app)

                        return redirect(f"/admin/user/mod/{category}?modded=True")
                    else:
                        return redirect(f"/admin/user/mod/{category}?usernameexist=True")
                elif category == "password":
                    new_password = request.form["new_password"]
                    if user.mod_:
                        if not admin.admin_:
                            return redirect(f"/admin/user/mod/{category}?ismod=True")

                    # we already know the user exists, so no "or_404" needed
                    user = Users.query.get(user.id)
                    user.password = encrypt_string(new_password)
                    db.session.commit()

                    return redirect(f"/admin/user/mod/{category}?modded=True")
                elif category == "chmod":
                    mod = request.form['mod_lvl']
                    if user.mod_:
                        if not admin.admin_:
                            return redirect(f"/admin/user/mod/{category}?ismod=True")

                    # we already know the user exists, so no "or_404" needed
                    user = Users.query.get(user.id)
                    user.mod_ = mod
                    db.session.commit()

                    return redirect(f"/admin/user/mod/{category}?modded=True")
                else:
                    return redirect(url_for("admin"))

    return redirect(url_for("index", notmod=True))


@app.route("/admin/")
def admin():
    if "id" in session and "mod" in session and not "guest" in session:
        return render_template("admin.html", session=[session])

    return redirect(url_for("index", notmod=True))


@app.route("/admin/user/delete")
def delete_user():
    if "id" in session and "mod" in session and not "guest" in session:
        if request.args.get('notfound'):
            flash("User not found.", "error")

        if request.args.get('userdeleted'):
            flash("User successfully deleted.", "info")

        if request.args.get('ismod'):
            flash("Cannot remove other mods.", "warning")

        if request.args.get('wrongpass'):
            flash("Password is incorrect.", "error")

        return render_template("delete_user.html", session=[session])
    return redirect(url_for("index", notmod=True))


@app.route("/admin/user/deleted/", methods=["GET", "POST"])
def remove_user():
    if "id" in session and "mod" in session and not "guest" in session:
        if request.method == "POST":  # if they logged in
            username = request.form["username"]
            admin_password = request.form["admin_password"]

            admin = Users.query.filter_by(
                username=session["username"]).all()[0]
            if admin.password != encrypt_string(admin_password):
                return redirect(url_for("delete_user", wrongpass=True))

            try:
                user = Users.query.filter_by(username=username).all()[
                    0]
            except IndexError:  # if user not found
                return redirect(url_for("delete_user", notfound=True))
            else:
                if user.mod_:
                    if not admin.admin_:
                        return redirect(url_for("delete_user", ismod=True))

                # remove all user torrents
                x = []
                for key, val in torrents.items():
                    if val["user"] == user.username:
                        x.append(key)

                for key in x:
                    torrents.pop(str(key))

                # we already know the user exists, so no "or_404" needed
                user = Users.query.get(user.id)
                db.session.delete(user)
                db.session.commit()

                write_torrent_json(torrents, app)
                return redirect(url_for("delete_user", userdeleted=True))

    return redirect(url_for("index", notmod=True))


@app.route("/admin/user/add")
def add_user():
    if "id" in session and "mod" in session and not "guest" in session:
        if request.args.get('added'):
            flash("Successfully added user.", "info")

        if request.args.get('usernameexist'):
            flash("Username already exists.", "error")

        return render_template("add_user.html", session=[session])
    return redirect(url_for("index", notmod=True))


@app.route("/admin/user/added/", methods=["GET", "POST"])
def create_user():
    if "id" in session and "mod" in session and not "guest" in session:
        if request.method == "POST":  # if they logged in
            username = request.form["username"]
            password = request.form["password"]
            # if there is at least 1 value in it, they're a mod
            is_mod = 0
            if len(request.form.getlist('is_mod')) == 1:
                is_mod = 1

            try:
                # this also checks if the user exists, we get an index error if they dont
                user = Users.query.filter_by(username=username).all()[
                    0]  # [0] so we don't get a list returned
            except IndexError:  # if user does not exist
                # insert data into database
                new_user = Users(username=username,
                                 password=encrypt_string(password), mod_=is_mod)
                db.session.add(new_user)  # adds content to database
                db.session.commit()  # save all changes to database

                return redirect(url_for("add_user", added=True))
            else:  # if user exists then:
                return redirect(url_for("add_user", usernameexist=True))

    return redirect(url_for("index", notmod=True))


@app.route("/signup/")
def signup():
    if request.args.get('usernameexist'):
        flash("Username already exists.", "error")

    return render_template("signup.html", no_nav=True)


@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":  # if they logged in
        username = request.form["uname"]
        password = request.form["pwd"]

        try:
            # this also checks if the user exists, we get an index error if they dont
            user = Users.query.filter_by(username=username).all()[
                0]  # [0] so we don't get a list returned
        except IndexError:  # if user does not exist
            # insert data into database
            new_user = Users(username=username,
                             password=encrypt_string(password))
            db.session.add(new_user)  # adds content to database
            db.session.commit()  # save all changes to database

            flash("Account has been created! Log in to get started.", "info")
        else:  # if user exists then:
            return redirect(url_for("signup", usernameexist=True))

    if request.args.get('auth') == "fail":
        flash("Username or password is incorrect", "error")

    return render_template("login.html", no_nav=True)


@app.route("/logout/")
def logout():
    session.pop("id", None)
    session.pop("mod", None)
    session.pop("username", None)
    session.pop("guest", None)

    return redirect(url_for("login"))


""" 
@app.route("/search", methods=["GET", "POST"])
def search_torrents():
    if request.method == "POST":
        search = request.form['search']
        found_word = []
        found_some = []
        for key, value in torrents.items():
            for _, i in value.items():
                if search == i:
                    found_word.append(key)
                    continue

                if search in i:
                    found_some.append(key)

        # remove duplicates
        found_word = list(dict.fromkeys(found_word))
        found_some = list(dict.fromkeys(found_some))

        for i in len(found_some):
            if found_some[i] in found_word:
                found_some.remove(found_some[i])

        results = []
        for i in found_word:
            results.append(torrents[str(i)])

        for i in found_some:
            results.append(torrents[str(i)])

        return render_template(f"index.html?search={search}", torrents=results, session=[session], rsc=remove_special_characters, search=True) 
"""


@app.route("/", methods=["GET", "POST"])
def index():
    rev_torrents = reverse_dict(torrents)

    if request.method == "POST":  # if they logged in
        username = request.form["uname"]
        password = request.form["pwd"]
        remember_me = request.form.getlist("remember_me")

        try:
            # this also checks if the user exists, we get an index error if they dont
            user = Users.query.filter_by(username=username).all()[
                0]  # [0] so we don't get a list returned
        except IndexError:
            return redirect(url_for("login", auth="fail"))

        if user.password == encrypt_string(password):
            session["id"] = user.id
            session["username"] = user.username
            if user.mod_:
                session["mod"] = user.mod_

            res = make_response(render_template("index.html", torrents=rev_torrents, session=[session], rsc=remove_special_characters))
            if remember_me:
                res.set_cookie("logged", value="here")
            return res
        else:
            return redirect(url_for("login", auth="fail"))

    if not "id" in session:  # if they didn't log in and is not logged in
        guest_sign_in()

    if request.args.get('deleted'):
        flash("Torrent Deleted.", "info")

    if request.args.get('guest'):
        flash("Only logged in users can use that feature.", "info")

    if request.args.get('notmod'):
        flash("Only mods may use that feature.", "warning")

    return render_template("index.html", torrents=rev_torrents, session=[session], rsc=remove_special_characters)


@app.route("/static/src/json/torrents.json")
@app.route("/static/src/json/config.json")
def protected():
    return redirect(url_for("index"))


@app.route("/user/")
def user():
    if "id" in session and not "guest" in session:
        if request.args.get('passchanged'):
            flash("Password changed successfully.", "info")

        return render_template("user.html", session=[session], torrents=torrents, rsc=remove_special_characters)
    return redirect(url_for("index", guest=True))


@app.route("/user/edit/username/")
def edit_username():
    if "id" in session and not "guest" in session:
        if request.args.get('found'):
            flash("Username already exists.", "error")

        if request.args.get('passed'):
            flash("Password is incorrect.", "error")

        return render_template("edit_user.html", session=[session], edit_username=True)
    return redirect(url_for("index", guest=True))


@app.route("/user/username/change/", methods=["GET", "POST"])
def change_username():
    if "id" in session and not "guest" in session:
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            name = Users.query.filter_by(username=username).all()

            if name:  # username already exists
                return redirect(url_for("edit_username", found=True))

            user = Users.query.get_or_404(session["id"])
            if user.password == encrypt_string(password):
                user.username = username
                db.session.commit()  # save all changes to database
            else:
                return redirect(url_for("edit_username", passed=True))

            for key, val in torrents.items():
                if(val["user"] == session["username"]):
                    val['user'] = username

            write_torrent_json(torrents, app)

            session["username"] = username

        return redirect(url_for("user"))
    return redirect(url_for("index", guest=True))


@app.route("/user/edit/password/")
def edit_password():
    if "id" in session and not "guest" in session:
        if request.args.get('passed'):
            flash("Password is incorrect.", "error")

        if request.args.get('cpass'):
            flash("Passwords do not match.", "warning")

        return render_template("edit_user.html", session=[session])
    return redirect(url_for("index", guest=True))


@app.route("/user/password/change/", methods=["GET", "POST"])
def change_password():
    if "id" in session and not "guest" in session:
        if request.method == "POST":
            new_password = request.form["password"]
            con_password = request.form["password_confirm"]
            old_password = request.form["old_password"]

            if not new_password == con_password:
                return redirect(url_for("edit_password", cpass=True))

            user = Users.query.get_or_404(session["id"])
            if user.password == encrypt_string(old_password):
                user.password = encrypt_string(new_password)
                db.session.commit()  # save all changes to database
            else:
                return redirect(url_for("edit_password", passed=True))

            return redirect(url_for("user", passchanged=True))
        return redirect(url_for("user"))
    return redirect(url_for("index", guest=True))


@app.route("/torrent/")
def torrent():
    if "id" in session and not "guest" in session:
        # if request.args.get('edit') == "true":
        #     return render_template("torrent-mod.html", session=[session])
        return render_template("torrent-mod.html", add_torrent=True, session=[session])
    return redirect(url_for("index", guest=True))


@app.route("/torrent/<int:tor_id>/")
def torrent_editing(tor_id):
    if "id" in session and not "guest" in session:
        return render_template("torrent-mod.html", data=torrents[str(tor_id)], tor_id=tor_id, session=[session])
    return redirect(url_for("index", guest=True))


@app.route("/torrent/del/<int:tor_id>/")
def confirm_delete(tor_id):
    if "id" in session and not "guest" in session:
        return render_template("confirm.html", tor_id=tor_id)
    return redirect(url_for("index", guest=True))


@app.route("/torrent/del/<int:tor_id>/confirmed", methods=["GET", "POST"])
def torrent_deleting(tor_id):
    if "id" in session and not "guest" in session:
        if torrents[str(tor_id)]["user"] == session["username"] or session["mod"]:
            torrents.pop(str(tor_id))

            write_torrent_json(torrents, app)

            return redirect(url_for("index", deleted=True))
        return redirect(url_for("index"))
    return redirect(url_for("index", guest=True))


@app.route("/torrent/add/", methods=["GET", "POST"])
def add_torrent():
    if "id" in session and not "guest" in session:
        if request.method == "POST":
            print(session["username"])
            try:
                torrents[str(int(list(torrents.keys())[-1]) + 1)] = {
                    "full_name": request.form["full-name"],
                    "name": request.form["display-name"],
                    "magnet": request.form["magnet"],
                    "size": request.form["file-size"],
                    "size_type": request.form["file-size-type"],
                    "type": request.form["file-type"],
                    "minor_type": request.form["file-type-minor"],
                    "desc": request.form["desc"],
                    "user": session["username"]
                }
            except IndexError:  # if torrent file is empty
                torrents["1"] = {
                    "full_name": request.form["full-name"],
                    "name": request.form["display-name"],
                    "magnet": request.form["magnet"],
                    "size": request.form["file-size"],
                    "size_type": request.form["file-size-type"],
                    "type": request.form["file-type"],
                    "minor_type": request.form["file-type-minor"],
                    "desc": request.form["desc"],
                    "user": session["username"]
                }

            write_torrent_json(torrents, app)

            return redirect(url_for("index"))
        return redirect(url_for("torrent"))
    return redirect(url_for("index", guest=True))


@app.route("/torrent/edit/<int:tor_id>/", methods=["GET", "POST"])
def edit_torrent(tor_id):
    # should be signed in and not as a guest
    if "id" in session and not "guest" in session:
        if request.method == "POST":
            user = torrents[str(tor_id)]['user']
            # user_id = torrents[str(tor_id)]['user_id']

            torrents.pop(str(tor_id))

            torrents[str(int(list(torrents.keys())[-1]) + 1)] = {
                "full_name": request.form["full-name"],
                "name": request.form["display-name"],
                "magnet": request.form["magnet"],
                "size": request.form["file-size"],
                "size_type": request.form["file-size-type"],
                "type": request.form["file-type"],
                "minor_type": request.form["file-type-minor"],
                "desc": request.form["desc"],
                "user": user
            }

            write_torrent_json(torrents, app)

            return redirect(url_for("index"))
        return redirect(url_for("torrent"))
    return redirect(url_for("index", guest=True))


if __name__ == "__main__":
    # REMEMBER TO CHANGE DATABASE IF WORKING LOCALLY
    if test_env:
        app.secret_key = 'testing_key'
        app.run(debug=True)
    else:
        app.run()