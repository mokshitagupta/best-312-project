from flask import Flask, render_template_string, render_template, request, Response, make_response, redirect, url_for
from pymongo import MongoClient
import bcrypt, random
from db import *

app = Flask(__name__)


def validate_user(auth_token):
    salt = getSalt()
    Check_Token = bcrypt.hashpw(auth_token.encode(), salt)
    exists, user = dbExist("feature", "sessionToken", Check_Token)

    print(f"user exists: {exists}, their auth token is {Check_Token}")
    # equivalent database.find_one(auth_token) #returns None if the user does not exist
    if exists:
        username = user["username"]
        return username
    else:
        return None


def like(post_id, username):
    post = dbQuery({"_id"}, post_id)
    likes = set(post["likes"])
    if username in likes:
        likes.remove(username)
    else:
        likes.add(username)
    likes = list(likes)
    update_likes = {"likes": likes}
    count = (len(likes))
    update_count = {"like_count": count}
    dbUpdate(update_likes, post_id)
    dbUpdate(update_count, post_id)
