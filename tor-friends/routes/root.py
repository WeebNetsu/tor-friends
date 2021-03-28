from flask import Blueprint, request, session, redirect, url_for, flash, render_template, make_response
from datetime import datetime

from ..auxillary import *
from ..databases.db import db
from ..databases.Users_db import Users

torrents = read_json_file("torrents")

root_page = Blueprint(
    "root", __name__, static_folder=f"{get_root()}static", template_folder=f"{get_root()}templates/root")


@root_page.route("/rules/")
def rules():
    if not "id" in session:
        guest_sign_in()

    return render_template("rules.html", session=[session])


@root_page.route("/signup/")
def signup():
    if request.args.get('usernameexist'):
        flash("Username already exists.", "error")

    return render_template("signup.html", no_nav=True)


@root_page.route("/login/", methods=["GET", "POST"])
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
            print("about to create")
            new_user = Users(username=username,
                             password=encrypt_string(password), date_accessed=datetime.today())
            db.session.add(new_user)  # adds content to database
            db.session.commit()  # save all changes to database

            flash("Account has been created! Log in to get started.", "info")
        else:  # if user exists then:
            return redirect(url_for("root.signup", usernameexist=True))

    if request.args.get('auth') == "fail":
        flash("Username or password is incorrect", "error")

    if request.args.get('acc_deleted'):
        flash("Account removal successful.", "info")

    return render_template("login.html", no_nav=True)


@root_page.route("/logout/")
def logout():
    session.pop("id", None)
    session.pop("mod", None)
    session.pop("username", None)
    session.pop("guest", None)

    if request.args.get('acc_deleted'):
        return redirect(url_for("root.login", acc_deleted=True))

    return redirect(url_for("root.login"))


@root_page.route("/", methods=["GET", "POST"])
def index():
    rev_torrents = reverse_dict(torrents)

    if request.method == "POST":  # if they logged in
        username = request.form["uname"]
        password = request.form["pwd"]
        # remember_me = request.form.getlist("remember_me")

        try:
            # this also checks if the user exists, we get an index error if they dont
            user = Users.query.filter_by(username=username).all()[
                0]  # [0] so we don't get a list returned
        except IndexError:
            return redirect(url_for("root.login", auth="fail"))

        if verify_encrypted_string(user.password, password):
            session["id"] = user.id
            session["username"] = user.username
            if user.mod_:
                session["mod"] = user.mod_

            res = make_response(render_template("index.html", torrents=rev_torrents, session=[
                                session], rsc=remove_special_characters))
            """ if remember_me:
                dt = datetime.now()
                td = timedelta(days=30) # keeps user signed in for 30 days
                exp_date = dt + td
                u_id = encrypt_string(str(session["id"]))
                res.set_cookie(
                    "logged",
                    value=u_id,
                    expires=exp_date
                ) """
            return res
        else:
            return redirect(url_for("root.login", auth="fail"))

    if not "id" in session:  # if they didn't log in and is not logged in
        guest_sign_in()

    if request.args.get('deleted'):
        flash("Torrent Deleted.", "info")

    if request.args.get('guest'):
        flash("Only logged in users can use that feature.", "info")

    if request.args.get('torrent_added'):
        flash("Hoorah! Torrent has been added!", "info")

    if request.args.get('torrent_modified'):
        flash("Torrent has been modified!", "info")

    if request.args.get('notmod'):
        flash("Only mods may use that feature.", "warning")

    return render_template("index.html", torrents=rev_torrents, session=[session], rsc=remove_special_characters)
