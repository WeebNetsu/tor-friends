import json
import re
import hashlib

# these functions should not interact with Flask (just to keep things simple)


def write_torrent_json(torrents, app):
    json_file = app.open_resource("static/src/json/torrents.json", 'w')
    # put json into file (will automatically convert DICT to JSON)
    json.dump(torrents, json_file, indent=4)
    json_file.close()


def remove_special_characters(str):
    return re.sub('[^A-Za-z0-9]+', '_', str)


def encrypt_string(str):
    sha_signature = hashlib.sha256(str.encode()).hexdigest()
    return sha_signature


def reverse_dict(dict_):
    rev_torrents = dict()
    for k, v in reversed(dict_.items()):
        rev_torrents[k] = v

    return rev_torrents
