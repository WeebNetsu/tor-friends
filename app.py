# push to heroku: https://www.youtube.com/watch?v=Li0Abz-KT78

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from collections import OrderedDict

import json

# my files
from auxillary import *

app = Flask(__name__)

# save in this folder
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tmp/users.db"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://bcc27f206e1efd:6cb2d273@us-cdbr-east-03.cleardb.com"
db = SQLAlchemy(app)  # link database and app


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.Text, nullable=False)
    mod_ = db.Column(db.Integer, nullable=False, default=0)  # 0 = false
    # admins are the only people who can remove mods
    admin_ = db.Column(db.Integer, nullable=False, default=0)

    # when you say BlogPost.query.all() the below will be returned
    def __repr__(self):
        return f"ID: {self.id}\nusername: {self.username}\npassword: {self.password}\nmod: {self.mod}"


db.create_all

# READING JSON FROM A FILE
json_data = open("static/src/json/torrents.json", 'r')
# will read from file (and convert to dictionary)
torrents = OrderedDict(json.load(json_data))
json_data.close()


session = {
    "id": 0,  # 0
    "username": None,  # "netsu",  # None
    "mod": False  # false
}
# NOTE: all render_templates shoudl include session EXCEPT for login


@app.route("/rules")
def rules():
    if session["id"] != 0:
        return render_template("rules.html", session=[session])

    return redirect("/login")


@app.route("/admin/user/mod/<string:category>")
def edit_user_details(category):
    if session["id"] != 0 and session["mod"]:
        if request.args.get('wrongpass'):
            return render_template("admin_mod_user.html", session=[session], category=category, wrongpass=True)

        if request.args.get('notfound'):
            return render_template("admin_mod_user.html", session=[session], category=category, notfound=True)

        if request.args.get('ismod'):
            return render_template("admin_mod_user.html", session=[session], category=category, ismod=True)

        if request.args.get('usernameexist'):
            return render_template("admin_mod_user.html", session=[session], category=category, usernameexist=True)

        if request.args.get('modded'):
            return render_template("admin_mod_user.html", session=[session], category=category, modded=True)

        return render_template("admin_mod_user.html", session=[session], category=category)

    return redirect("/")


@app.route("/admin/mod/user/set/<string:category>", methods=["GET", "POST"])
def set_user_details(category):
    if session["id"] != 0 and session["mod"]:
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

                        write_torrent_json(torrents)

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
                    return redirect("/admin")

    return redirect("/")


@app.route("/admin")
def admin():
    if session["id"] != 0 and session["mod"]:
        return render_template("admin.html", session=[session])

    return redirect("/")


@app.route("/admin/user/delete")
def delete_user():
    if session["id"] != 0 and session["mod"]:
        if request.args.get('notfound'):
            return render_template("delete_user.html", notfound=True, session=[session])

        if request.args.get('userdeleted'):
            return render_template("delete_user.html", userdeleted=True, session=[session])

        if request.args.get('ismod'):
            return render_template("delete_user.html", ismod=True, session=[session])

        if request.args.get('wrongpass'):
            return render_template("delete_user.html", wrongpass=True, session=[session])

        return render_template("delete_user.html", session=[session])
    return redirect("/")


@app.route("/admin/user/deleted", methods=["GET", "POST"])
def remove_user():
    if session["id"] != 0 and session["mod"]:
        if request.method == "POST":  # if they logged in
            username = request.form["username"]
            admin_password = request.form["admin_password"]

            admin = Users.query.filter_by(
                username=session["username"]).all()[0]
            if admin.password != encrypt_string(admin_password):
                return redirect("/admin/user/delete?wrongpass=True")

            try:
                user = Users.query.filter_by(username=username).all()[
                    0]
            except IndexError:  # if user not found
                return redirect("/admin/user/delete?notfound=True")
            else:
                if user.mod_:
                    if not admin.admin_:
                        return redirect("/admin/user/delete?ismod=True")

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

                write_torrent_json(torrents)
                return redirect("/admin/user/delete?userdeleted=True")

    return redirect("/")


@app.route("/admin/user/add")
def add_user():
    if session["id"] != 0 and session["mod"]:
        if request.args.get('added'):
            return render_template("add_user.html", useradded=True, session=[session])

        if request.args.get('usernameexist'):
            return render_template("add_user.html", exsists=True, session=[session])

        return render_template("add_user.html", session=[session])
    return redirect("/")


@app.route("/admin/user/added", methods=["GET", "POST"])
def create_user():
    if session["id"] != 0 and session["mod"]:
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

                return redirect("/admin/user/add?added=True")
            else:  # if user exists then:
                return redirect("/admin/user/add?usernameexist=True")

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.args.get('auth') == "fail":
        return render_template("login.html", no_nav=True, fail=True)

    return render_template("login.html", no_nav=True)


@app.route("/logout")
def logout():
    session["id"] = 0
    session["mod"] = False
    session["username"] = None

    return redirect("/login")


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
        try:
            # this also checks if the user exists, we get an index error if they dont
            user = Users.query.filter_by(username=username).all()[
                0]  # [0] so we don't get a list returned
        except IndexError:
            return redirect("/login?auth=fail")

        if user.password == encrypt_string(password):
            session["id"] = user.id
            session["mod"] = user.mod_
            session["username"] = user.username
            return render_template("index.html", torrents=rev_torrents, session=[session], rsc=remove_special_characters)
        else:
            return redirect("/login?auth=fail")

    if session["id"] != 0:
        if request.args.get('del'):
            return render_template("index.html", torrents=rev_torrents, session=[session], tor_deleted=True, rsc=remove_special_characters)
        return render_template("index.html", torrents=rev_torrents, session=[session], rsc=remove_special_characters)
    return redirect("/login")


# app.view_functions['static'] = redirect("/")
@app.route("/static/src/json/torrents.json")
def protected():
    return redirect("/")


@app.route("/user")
def user():
    if session["id"] != 0:
        if request.args.get('passchanged'):
            return render_template("user.html", session=[session], torrents=torrents, rsc=remove_special_characters, newpass=True)

        return render_template("user.html", session=[session], torrents=torrents, rsc=remove_special_characters)
    return redirect("/login")


@app.route("/user/edit/username")
def edit_username():
    if session["id"] != 0:
        if request.args.get('found'):
            return render_template("edit_user.html", session=[session], edit_username=True, exsists=True)

        if request.args.get('pass'):
            return render_template("edit_user.html", session=[session], edit_username=True, invalid_pass=True)

        return render_template("edit_user.html", session=[session], edit_username=True)
    return redirect("/login")


@app.route("/user/username/change", methods=["GET", "POST"])
def change_username():
    if session["id"] != 0:
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            name = Users.query.filter_by(username=username).all()

            if name:  # username already exists
                return redirect("/user/edit/username?found=True")

            user = Users.query.get_or_404(session["id"])
            if user.password == encrypt_string(password):
                user.username = username
                db.session.commit()  # save all changes to database
            else:
                return redirect("/user/edit/username?pass=True")

            for key, val in torrents.items():
                if(val["user"] == session["username"]):
                    val['user'] = username

            write_torrent_json(torrents)

            session["username"] = username

            return redirect("/user")
        return redirect("/user")
    return redirect("/login")


@app.route("/user/edit/password")
def edit_password():
    if session["id"] != 0:
        if request.args.get('pass'):
            return render_template("edit_user.html", session=[session], invalid_pass=True)

        if request.args.get('cpass'):
            return render_template("edit_user.html", session=[session], no_match_pass=True)

        return render_template("edit_user.html", session=[session])
    return redirect("/login")


@app.route("/user/password/change", methods=["GET", "POST"])
def change_password():
    if session["id"] != 0:
        if request.method == "POST":
            new_password = request.form["password"]
            con_password = request.form["password_confirm"]
            old_password = request.form["old_password"]

            if not new_password == con_password:
                return redirect("/user/edit/password?cpass=True")

            user = Users.query.get_or_404(session["id"])
            if user.password == encrypt_string(old_password):
                user.password = encrypt_string(new_password)
                db.session.commit()  # save all changes to database
            else:
                return redirect("/user/edit/password?pass=True")

            return redirect("/user?passchanged=True")
        return redirect("/user")
    return redirect("/login")


@app.route("/torrent")
def torrent():
    if session["id"] != 0:
        return render_template("torrent-mod.html", add_torrent=True, session=[session])
        if request.args.get('edit') == "true":
            return render_template("torrent-mod.html", session=[session])
    return redirect("/login")


@app.route("/torrent/<int:tor_id>")
def torrent_editing(tor_id):
    if session["id"] != 0:
        return render_template("torrent-mod.html", data=torrents[str(tor_id)], tor_id=tor_id, session=[session])
        # if request.args.get('edit') == "true":
        # return render_template("torrent-mod.html")
    return redirect("/login")


@app.route("/torrent/del/<int:tor_id>")
def torrent_deleting(tor_id):
    if session["id"] != 0:
        if torrents[str(tor_id)]["user"] == session["username"] or session["mod"]:
            torrents.pop(str(tor_id))

            write_torrent_json(torrents)

            return redirect("/?del=True")
        return redirect("/")
    return redirect("/login")


@app.route("/torrent/add", methods=["GET", "POST"])
def add_torrent():
    if session["id"] != 0:
        if request.method == "POST":

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

            write_torrent_json(torrents)

            return redirect("/")
        return redirect("/torrent")
    return redirect("/login")


@app.route("/torrent/edit/<int:tor_id>", methods=["GET", "POST"])
def edit_torrent(tor_id):
    if session["id"] != 0:
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

            write_torrent_json(torrents)

            return redirect("/")
        return redirect("/torrent")
    return redirect("/login")


if __name__ == "__main__":
    app.run()
