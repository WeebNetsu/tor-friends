import json
import re
import hashlib
import binascii
import os
import random

from collections import OrderedDict
from flask import flash, session


def guest_sign_in():
    session["id"] = random.randint(1, 999999)  # guest random ID
    session["username"] = "Guest"
    session["guest"] = True
    flash("Signed in as Guest user", "info")


def get_root():
    return os.path.realpath(__file__)[:-len(os.path.basename(__file__))]


def read_json_file(file):
    try:
        json_data = open(f"{get_root()}static/src/json/{file}.json", 'r')
        # will read from file (and convert to dictionary)
        torrents = OrderedDict(json.load(json_data))
        json_data.close()
    except FileNotFoundError:
        # erase everything and rewrite the file
        tFile = open(f"{get_root()}static/src/json/{file}.json", 'w')
        tFile.write("{\n}")
        tFile.close()

        json_data = open(f"{get_root()}static/src/json/{file}.json", 'r')
        # will read from file (and convert to dictionary)
        torrents = OrderedDict(json.load(json_data))
        json_data.close()

    return torrents

# these functions should not interact with Flask (just to keep things simple)


def write_torrent_json(torrents):
    with open(f"{get_root()}/static/src/json/torrents.json", "w") as json_file:
        json.dump(torrents, json_file, indent=4)


def remove_special_characters(str_):
    return re.sub('[^A-Za-z0-9]+', '_', str_)


def encrypt_string(str_):  # hash the string
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    str_hash = hashlib.pbkdf2_hmac(
        'sha512', str_.encode('utf-8'), salt, 100000)
    str_hash = binascii.hexlify(str_hash)
    return (salt + str_hash).decode('ascii')


def verify_encrypted_string(stored_str, provided_str):  # verify string
    # verify_encrypted_string(hashed_str, "string to be compared")
    salt = stored_str[:64]
    stored_str = stored_str[64:]
    str_hash = hashlib.pbkdf2_hmac('sha512', provided_str.encode(
        'utf-8'), salt.encode('ascii'), 100000)
    str_hash = binascii.hexlify(str_hash).decode('ascii')
    return str_hash == stored_str

# def encrypt_string(str):
#     sha_signature = hashlib.sha256(str.encode()).hexdigest()
#     return sha_signature


def reverse_dict(dict_):
    rev_torrents = dict()
    for k, v in reversed(dict_.items()):
        rev_torrents[k] = v

    return rev_torrents
