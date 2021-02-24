from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import json
from collections import OrderedDict


app = Flask(__name__)

# save in this folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///posts.db"
db = SQLAlchemy(app)  # link database and app


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    mod = db.Column(db.Integer, nullable=False, default=0)  # 0 = false

    # when you say BlogPost.query.all() the below will be returned
    def __repr__(self):
        return f"ID: {self.id}\nusername: {self.username}\npassword: {self.password}\nmod: {self.mod}"


# READING JSON FROM A FILE
json_data = open("static/src/json/torrents.json", 'r')
# will read from file (and convert to dictionary)
torrents = OrderedDict(json.load(json_data))
json_data.close()
# print()

session = {
    "logged_in": False,
    "id": 1,  # 0
    "username": "netsu",  # None
    "mod": True  # false
}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.args.get('auth') == "fail":
        return render_template("login.html", no_nav=True, fail=True)

    return render_template("login.html", no_nav=True)


@app.route("/logout")
def logout():
    session["logged_in"] = False
    session["id"] = 0
    session["mod"] = False
    session["username"] = None

    return redirect("/login")


@app.route("/", methods=["GET", "POST"])
def index():
    rev_torrents = dict()
    for k, v in reversed(torrents.items()):
        rev_torrents[k] = v
    if request.method == "POST":  # if they're logged in
        table = User.query.all()
        username = request.form["uname"]
        password = request.form["pwd"]
        for row in table:
            if row.username == username:
                if row.password == password:
                    session["logged_in"] = True
                    session["id"] = row.id
                    session["mod"] = row.mod
                    session["username"] = row.username
                    return render_template("index.html", torrents=rev_torrents, session=[session])
        return redirect("/login?auth=fail")

    if session["id"] != 0:
        return render_template("index.html", torrents=rev_torrents, session=[session])
    return redirect("/login")


@app.route("/user")
def user():
    if session["id"] != 0:
        return render_template("user.html", session=[session], torrents=torrents)
    return redirect("/login")


# @app.route("/user/edit/username")
# def edit_username():
#     if session["id"] != 0:
#         return render_template("edit-username.html", session=[session])
#     return redirect("/login")

@app.route("/torrent")
def torrent():
    if session["id"] != 0:
        return render_template("torrent-mod.html", add_torrent=True)
        if request.args.get('edit') == "true":
            return render_template("torrent-mod.html")
    return redirect("/login")


@app.route("/torrent/<int:tor_id>")
def torrent_editing(tor_id):
    if session["id"] != 0:
        return render_template("torrent-mod.html", data=torrents[str(tor_id)], tor_id=tor_id)
        # if request.args.get('edit') == "true":
        # return render_template("torrent-mod.html")
    return redirect("/login")


@app.route("/torrent/add", methods=["GET", "POST"])
def add_torrent():
    if session["id"] != 0:
        if request.method == "POST":
            torrents[str(len(torrents) + 1)] = {
                "user_id": session["id"],
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

            new_file = open("static/src/json/torrents.json", "w")
            # put json into file (will automatically convert DICT to JSON)
            json.dump(torrents, new_file, indent=4)
            new_file.close()

            return redirect("/")
        return redirect("/torrent")
    return redirect("/login")


@app.route("/torrent/edit/<int:tor_id>", methods=["GET", "POST"])
def edit_torrent(tor_id):
    if session["id"] != 0:
        if request.method == "POST":
            torrents.pop(str(tor_id))

            torrents[str(len(torrents) + 1)] = {
                "user_id": session["id"],
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

            new_file = open("static/src/json/torrents.json", "w")
            # put json into file (will automatically convert DICT to JSON)
            json.dump(torrents, new_file, indent=4)
            new_file.close()

            return redirect("/")
        return redirect("/torrent")
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
