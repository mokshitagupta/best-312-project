from flask import Flask, render_template_string, render_template, request, Response, make_response, redirect, url_for
from pymongo import MongoClient
import bcrypt, random, html
from db import *

class ConfigClass(object):
    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'



def create_app():
    
    # Setup Flask and load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        # String-based templates
        name = request.cookies.get('token')
        if name == None:
            #no auth token
            return render_template('register.html')
        
        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())
        query = dbQuery("hash",salted, raw=True)
        if len(query) == 0:
            return render_template('register.html')
        
        else:
            exists, entry =  getUserEntry("path", "registeredUsers", query[0]["username"], all=True)
            print(exists, entry)
            return render_template('profile.html', username=entry["username"], username_hidden=entry["username"])

    
    @app.route('/register', methods=['POST',"GET"])
    def register():
        if request.method == "POST" :
            form = request.form
            username = form["username"]
            password = form["password"]

            exists = dbQuery("username", username, all=False, raw=True) != []
            if exists:
                return render_template('register.html', feedback="user already in db"),401
            
            s = getSalt()

            userEntry = {
                "_id" : increment(),
                "path" : "registeredUsers",
                "username": html.escape(username),
                "password" : bcrypt.hashpw(password.encode(), s),
                "xsrf": "".join([str(random.randint(0,9) )for _ in range(5)])
            }

            print(userEntry, " <----- inserted to db")
            dbInsert(userEntry)
            return render_template('register.html', feedback="registration successful"),200
            
        else:
        # String-based templates
            
            return render_template('register.html')
    
    @app.route('/login', methods=['POST',"GET"])
    def login():
        if request.method == "POST" :
            form = request.form
            username = form["username"]
            password = form["password"]

            entry = dbQuery("username", username, all=False, raw=True)
            # salt =  dbQuery("feature", "salt", all=False, raw=True)
            exists = entry != []

            if not exists:
                return render_template('register.html', login_feedback="user not in db"),404

            #verify passwords
            verif = bcrypt.checkpw(password.encode("utf-8"), entry["password"])
            # #print("ABLE TO VERIFY PASSWORD !!!")
            if not verif:
                return render_template('register.html', login_feedback="invalid credentials"),403

            token  = "".join([str(random.randint(0,9) )for _ in range(10)])
            s = getSalt()
            hash = bcrypt.hashpw(token.encode("utf-8"), s)

            insertSessionId(hash, username)
            
            response = make_response(redirect(url_for("home_page")))
            response.set_cookie("token", value = token, max_age = 60 * 60 * 24, httponly = True)

            return response
        else :
            return render_template('register.html')


    @app.route('/add-post', methods=["POST"])
    def addPost():
        form = request.form
        title = form["title"]
        detail = form["detail"]
        username = form["username"]
        name = request.cookies.get('token')

        entry = {
            "_id" : increment(),
            "title": html.escape(title),
            "detail" : html.escape(detail),
            "username" : html.escape(username),
            "feature":"posts"
        }

        print(name, "nameeurd", getSalt())


        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())

        # print(dbQuery("feature","sessionToken", raw=True), salted)

        if len(dbQuery("hash",salted, raw=True)) == 0:
            return redirect(request.referrer), 403
        

        dbInsert(entry)
        comments = dbQuery("feature", "posts", all=True, raw=True)

        return redirect(request.referrer)

    @app.route('/get-posts', methods=["GET"])
    def getPosts():

        comments = dbQuery("feature", "posts", all=True, raw=True)
        return comments

    @app.route('/like', methods=["POST"])
    def likePost():
        authToken = request.cookies.get('token')
        salted = bcrypt.hashpw(authToken.encode("utf-8"), getSalt())
        user = dbQuery("hash", salted, raw=True)
        if len(user) == 0:
            return redirect(request.referrer), 403
        exists, entry = getUserEntry("path", "registeredUsers", user[0]["username"], all=True)
        if exists is True:
            username = entry["username"]
            
    return app


# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
