from flask import Flask, render_template_string, render_template, request, Response, make_response, redirect, url_for
from pymongo import MongoClient
import bcrypt, random
from db import *

app = Flask(__name__)

mongo_client = MongoClient('localhost', 27017)


def validate_user(auth_token):
    exists, user = dbExist("feature","sessionToken", auth_token) # equivalent database.find_one(auth_token) #returns None if the user does not exist
    if exists:
        username = user["username"]
        return username
    else:
        return None

def like(self, post_id, username):
    post = dbQuery("_id", post_id)
    likes = set(post["likes"])
    if username in likes:
        likes.remove(username)
    else:
        likes.add(username)
    likes = list(likes)
    dbUpdate("likes", likes)
    count = (len(likes))
    return count