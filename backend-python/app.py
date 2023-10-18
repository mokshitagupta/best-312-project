from flask import Flask, render_template_string, render_template, request, Response, make_response, redirect, url_for
from pymongo import MongoClient
import bcrypt, random
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
        return """
                <h2>Home page</h2>
                <p><a href="/register">Register</a></p>
                <p><a href="/login">Login</a></p>
            """
    
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
                "username": username,
                "password" : bcrypt.hashpw(password.encode(), s),
                "xsrf": "".join([str(random.randint(0,9) )for _ in range(5)])
            }

            print(userEntry, " <----- inserted to db")
            dbInsert(userEntry)
            return redirect(url_for("login"))

            # return render_template('register.html', feedback="Account succesfully created"),200        
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
                return render_template('login.html', feedback="user not in db"),404

            #verify passwords
            verif = bcrypt.checkpw(password.encode("utf-8"), entry["password"])
            # #print("ABLE TO VERIFY PASSWORD !!!")
            if not verif:
                return render_template('login.html', feedback="invalid credentials"),403

            token  = "".join([str(random.randint(0,9) )for _ in range(10)])
            s = getSalt()
            hash = bcrypt.hashpw(token.encode(), s)

            insertSessionId(hash, username)

            # resp = make_response(render_template('profile.html', username=username))
            
            response = make_response(redirect(url_for("profilePage",id=str(entry["_id"]))))
            response.set_cookie("token", value = token, max_age = 60 * 60 * 24, httponly = True)

            return response
        else :
            return render_template('login.html')


    @app.route('/profile/<id>')
    def profilePage(id):
        # String-based templates
        entry =  dbQuery("_id", int(id), all=False, raw=True)
        print(entry,id)
        return render_template('profile.html', username=entry["username"], username_hidden=entry["username"])

    @app.route('/add-post', methods=["POST"])
    def addPost():
        form = request.form
        title = form["title"]
        detail = form["detail"]
        username = form["username"]
        name = request.cookies.get('token')

        entry = {
            "_id" : increment(),
            "title":title,
            "detail" : detail,
            "username" : username,
            "feature":"posts"
        }
        

        dbInsert(entry)
        comments = dbQuery("feature", "posts", all=True, raw=True)

        return redirect(request.referrer)

    @app.route('/get-posts', methods=["GET"])
    def getPosts():

        comments = dbQuery("feature", "posts", all=True, raw=True)
        return comments

    
    return app


# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
