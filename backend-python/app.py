import json

from flask import Flask, flash, render_template_string, render_template, request, Response, make_response, redirect, url_for
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import bcrypt, random, html, os
from db import *
import datetime

UPLOAD_FOLDER = './static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class ConfigClass(object):
    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'


def create_app():
    # Setup Flask and load app.config
    app = Flask(__name__)
    app.config.from_object(__name__ + '.ConfigClass')

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        # String-based templates
        name = request.cookies.get('token')
        if name == None:
            # no auth token
            return render_template('register.html')

        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())
        query = dbQuery("hash", salted, raw=True)
        if len(query) == 0:
            return render_template('register.html')

        else:
            exists, entry = getUserEntry("path", "registeredUsers", query[0]["username"], all=True)
            print(exists, entry)
            return render_template('comments.html', username=entry["username"], username_hidden=entry["username"])
        
    @app.route('/create')
    def create():
        name = request.cookies.get('token')
        if name == None:
            # no auth token
            return render_template('register.html')

        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())
        query = dbQuery("hash", salted, raw=True)
        if len(query) == 0:
            return render_template('register.html')

        else:
            exists, entry = getUserEntry("path", "registeredUsers", query[0]["username"], all=True)
            print(exists, entry)
            return render_template('profile.html', username=entry["username"], username_hidden=entry["username"])

    @app.route('/register', methods=['POST', "GET"])
    def register():
        if request.method == "POST":
            form = request.form
            username = form["username"]
            password = form["password"]

            exists = dbQuery("username", username, all=False, raw=True) != []
            if exists:
                return render_template('register.html', feedback="user already in db"), 401

            s = getSalt()

            userEntry = {
                "_id": increment(),
                "path": "registeredUsers",
                "username": html.escape(username),
                "password": bcrypt.hashpw(password.encode(), s),
                "xsrf": "".join([str(random.randint(0, 9)) for _ in range(5)])
            }

            print(userEntry, " <----- inserted to db")
            dbInsert(userEntry)
            return render_template('register.html', feedback="registration successful"), 200

        else:
            # String-based templates

            return render_template('register.html')

    @app.route('/login', methods=['POST', "GET"])
    def login():
        if request.method == "POST":
            form = request.form
            username = form["username"]
            password = form["password"]

            entry = dbQuery("username", username, all=False, raw=True)
            # salt =  dbQuery("feature", "salt", all=False, raw=True)
            exists = entry != []

            if not exists:
                return render_template('register.html', login_feedback="user not in db"), 404

            # verify passwords
            verif = bcrypt.checkpw(password.encode("utf-8"), entry["password"])
            # #print("ABLE TO VERIFY PASSWORD !!!")
            if not verif:
                return render_template('register.html', login_feedback="invalid credentials"), 403

            token = "".join([str(random.randint(0, 9)) for _ in range(10)])
            s = getSalt()
            hash = bcrypt.hashpw(token.encode("utf-8"), s)

            insertSessionId(hash, username)

            response = make_response(redirect(url_for("home_page")))
            response.set_cookie("token", value=token, max_age=60 * 60 * 24, httponly=True)

            return response
        else:
            return render_template('register.html')
        
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/add-post', methods=["POST"])
    def addPost():
        form = request.form
        title = form["title"]
        detail = form["detail"]
        username = form["username"]
        img = request.files["image"]
        filename = secure_filename(img.filename)
        price = form["price"]
        duration_hours = form["duration_hours"]
        duration_minutes = form["duration_minutes"]
        name = request.cookies.get('token')
        
        duration = datetime.datetime.now() + datetime.timedelta(hours=int(duration_hours), minutes=int(duration_minutes))
        
        exists, entry = getUserEntry("path", "registeredUsers", username, all=True)
        
        if img and allowed_file(img.filename) and exists:
            entry = {
                "_id": increment(),
                # "user_id": entry["_id"],
                "username": html.escape(username),
                "title": html.escape(title),
                "detail": html.escape(detail),
                "pic" : filename,
                "price": html.escape(price),
                "duration": duration.strftime("%m/%d/%Y %H:%M:%S"),
                "winner": "",
                "active": True,
                "timestamp": datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                "feature": "posts",
                "likes": []
            }

            img.save(os.path.join(UPLOAD_FOLDER, filename))

        print(name, "nameeurd", getSalt())

        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())

        # print(dbQuery("feature","sessionToken", raw=True), salted)

        if len(dbQuery("hash", salted, raw=True)) == 0:
            return redirect(request.referrer), 403

        dbInsert(entry)
        comments = dbQuery("feature", "posts", all=True, raw=True)
        
        print("db: ", getDB())

        return redirect(request.referrer)

    @app.route('/get-posts', methods=["GET"])
    def getPosts():
        comments = dbQuery("feature", "posts", all=True, raw=True)
        return json.dumps(comments)

    @app.route('/like', methods=["POST"])
    def likePost():
        postID = request.json['id']
        print(f"post ID = {postID}")
        authToken = request.cookies.get('token')
        salted = bcrypt.hashpw(authToken.encode("utf-8"), getSalt())
        userDocument = dbQuery("hash", salted, raw=True)[0]
        username = userDocument["username"]
        print(f"user doc = {userDocument},\nusername = {username}")
        if len(userDocument) == 0:
            return redirect(request.referrer), 403
        else:
            post = dbQuery("_id", postID, all=False, raw=True)
            # print(f"query = " + dbQuery("_id", postID, all=False, raw=True))
            print(f"post = {post}")
            likesUpdater = post["likes"]
            print(f"likes = {likesUpdater}")
            if username not in likesUpdater:
                likesUpdater.append(username)
            else:
                likesUpdater.remove(username)
            updateVal = {"likes": likesUpdater}
            dbUpdate(postID, updateVal)
            return ""

    @app.route('/auctions-won', methods=["GET"])
    def getPostsWon():
        authToken = request.cookies.get('token')
        salted = bcrypt.hashpw(authToken.encode("utf-8"), getSalt())
        userDocument = dbQuery("hash", salted, raw=True)[0]
        username = userDocument["username"]
        if len(userDocument) == 0:
            return redirect(request.referrer), 403
        else:
            wonPosts = dbQuery("winner", username, all=True, raw=True)
            return json.dumps(wonPosts)

    @app.route('/auctions-created', methods=["GET"])
    def getPostsCreated():
        authToken = request.cookies.get('token')
        salted = bcrypt.hashpw(authToken.encode("utf-8"), getSalt())
        userDocument = dbQuery("hash", salted, raw=True)[0]
        username = userDocument["username"]
        if len(userDocument) == 0:
            return redirect(request.referrer), 403
        else:
            createdPosts = dbQuery("username", username, all=True, raw=True)
            return json.dumps(createdPosts)
        pass

    return app


# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
