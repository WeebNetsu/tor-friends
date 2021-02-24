from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import json


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
        return f"ID: {self.id}\nusername: {self.username}\npassword: {self.password}\nmod: {self.username}"


# READING JSON FROM A FILE
json_data = open("static/src/json/torrents.json", 'r')
# will read from file (and convert to dictionary)
torrents = json.load(json_data)
json_data.close()
# print()

session = {
    "logged_in": False,
    "id": 0
}


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.args.get('auth') == "fail":
        return render_template("login.html", no_nav=True, fail=True)

    return render_template("login.html", no_nav=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        table = User.query.with_entities(
            User.id, User.username, User.password).all()
        username = request.form["uname"]
        password = request.form["pwd"]
        for row in table:
            if row[1] == username:
                if row[2] == password:
                    session["logged_in"] = True
                    session["id"] = row[0]
                    return render_template("index.html", torrents=torrents)
        return redirect("/login?auth=fail")

    if session["id"] != 0:
        return render_template("index.html", torrents=torrents)
    return redirect("/login")


@app.route("/user")
def user():
    return render_template("user.html")


@app.route("/torrent/add")
def add_torrent():
    return render_template("torrent-mod.html", add_torrent=True)


if __name__ == "__main__":
    app.run(debug=True)
