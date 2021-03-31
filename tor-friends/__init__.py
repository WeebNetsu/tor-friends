from flask import Flask, redirect, url_for  # , send_from_directory

import json

from .databases.db import db

from .routes.admin import admin_page
from .routes.torrent import torrent_page
from .routes.user import user_page
from .routes.root import root_page

app = Flask(__name__)
test_env = True  # if i'm using a test environment

with app.open_resource("static/json/config.json", 'r') as json_data:
    config_data = json.load(json_data)
    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqltype://username:password@host/database"
    if test_env:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tmp/users.db"
        app.secret_key = 'testing_key'
        print("\t\tUsing Testing Environment")
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = config_data["database"]

app.url_map.strict_slashes = False  # doesn't force a "/" at the end of a link
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Blueprints
app.register_blueprint(admin_page, url_prefix="/admin")
app.register_blueprint(torrent_page, url_prefix="/torrent")
app.register_blueprint(user_page, url_prefix="/user")
app.register_blueprint(root_page, url_prefix="/")

# @app.route("/ads.txt")
# def ads(): # so ads.txt can be accessed by ad website
# 	return send_from_directory("static", "ads.txt")


@app.route("/static/json/torrents.json")
@app.route("/static/json/config.json")
def protected():
    return redirect(url_for("index"))

# if __name__ == "__main__":
# if test_env:
#     app.secret_key = 'testing_key'
#     app.run(debug=True)
# else:
#     app.run()
