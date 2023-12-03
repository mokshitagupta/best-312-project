import json

from flask import Flask, flash, render_template_string, render_template, request, Response, make_response, redirect, url_for, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import bcrypt, random, html, os
from db import *
import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class ConfigClass(object):
    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'


def create_app():
    # Setup Flask and load app.config
    app = Flask(__name__)
    app.config.from_object(__name__ + '.ConfigClass')
    socketio = SocketIO(app)

    limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per second"],
    storage_uri="memory://",
)

    @socketio.on('time')
    def handle_message(data):
        id = data["id"]
        entry = dbQuery("_id", id, all=False, raw=True)

        #this is probably where the post auction clean up code will need to be added for LO3
        if len(entry) > 0:
            rem =  datetime.datetime.strptime(entry["duration"], "%m/%d/%Y %H:%M:%S") - datetime.datetime.now()
            retTime = int(rem.total_seconds())
            if retTime < 0:
                dbUpdate(id, {"active":False})
                dbUpdate(id, {"finalWinner": entry["winner"]})
                dbUpdate(id, {"winningBid": entry["highestBid"]})
            return retTime
        else:
            return -1
        
    @socketio.on('submitBid')
    def submit_bid(data):
        #data -> post id
        entry = dbQuery("_id", data["_id"], all=False, raw=True)
        try:
            bid = int(data["bid"])
        except:
            bid = 0

        #verification
        name = request.cookies.get('token')
       
        if name == None:
            # no auth token
            return {"updated":"redirect"}

        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())
        query = dbQuery("hash", salted, raw=True)
        if len(query) == 0:
            return {"updated":"redirect"}

        else:


            exists, userinfo = getUserEntry("path", "registeredUsers", query[0]["username"], all=True)
            print(exists, entry, userinfo, bid)

            if entry["active"] == True:
                if "highestBid" not in entry:
                    print("sorry that you have to grade this :( love u <3")


                    
                elif bid > entry["highestBid"]:
                    # id: id instead of the {'highestBid': {"$exists" : False}}
                    dbUpdate( data["_id"], {"highestBid":bid})
                    dbUpdate( data["_id"], {"winner":userinfo["username"]})
                    return {"updated":True, "bid":bid, "winner":userinfo["username"]}
                
            else:
                return {"updated":False, "bid":entry["highestBid"], "winner":entry["winner"]}

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
                "finalWinner": "N/A",
                "winningBid": "(Auction still active)",
                "active": True,
                "timestamp": datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                "feature": "posts",
                "likes": [],
                "highestBid":0,
            }

            img.save(os.path.join(app.root_path, UPLOAD_FOLDER, filename))

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
        if authToken:
            salted = bcrypt.hashpw(authToken.encode("utf-8"), getSalt())
            userDocument = dbQuery("hash", salted, raw=True)[0]
            username = userDocument["username"]
            print(f"username = {username}")
            if len(userDocument) == 0:
                return redirect(request.referrer), 403
            else:
                createdPosts = dbQuery("feature", "posts", all=True, raw=True)
                for i in createdPosts:
                    if i["finalWinner"] != username:
                        createdPosts.remove(i)
                print(f"created posts:/n{createdPosts}")
                return json.dumps(createdPosts)

    @app.route('/auctions-created', methods=["GET"])
    def getPostsCreated():
        authToken = request.cookies.get('token')
        if authToken:
            salted = bcrypt.hashpw(authToken.encode("utf-8"), getSalt())
            userDocument = dbQuery("hash", salted, raw=True)[0]
            username = userDocument["username"]
            print(f"username = {username}")
            if len(userDocument) == 0:
                return redirect(request.referrer), 403
            else:
                createdPosts = dbQuery("feature", "posts", all=True, raw=True)
                for i in createdPosts:
                    if i["username"] != username:
                        createdPosts.remove(i)
                print(f"created posts:/n{createdPosts}")
                return json.dumps(createdPosts)

    @app.route('/post/<int:Number>')
    def allow(Number):
        entry = dbQuery("_id", Number, all=False, raw=True)
        
        if len(entry) > 0:
            print(entry)
            winner = entry["winner"]
            if winner == "":
                winner = "No bids yet :("
            return render_template('auction.html', img ="/static/uploads/"+entry["pic"],title=entry["title"],
                                    creator=entry["username"], id=Number, description=entry["detail"],
                                    price=entry["price"], curr_highest=entry["highestBid"], winner=winner)
        else:
            return "Auction not found :("
        
    @app.route('/user_dashboard')
    def user_dashboard():
        return render_template('user.html')
    
    
    @app.route('/logout')
    def logout():
        resplog = make_response(redirect('/'))  
        resplog.set_cookie('token', '', expires=0) 
        return resplog

    @app.before_request
    @limiter.limit("10 per second")
    def attack():
        # Forward = request.headers.get('X-Forwarded-For')
        # ip_address = request.headers.get('X-Real-IP')
        # hope = request.headers.get('X-hope')
        # sanity = request.headers.get('Sanity-Check')

        print("Full Request:", request, file=sys.stderr)

        for i in request.headers:
            print("header = ", i, file=sys.stderr)
        for i in request.environ:
            print("enviorn = ", i, file=sys.stderr)
        for i in request.remote_addr:
            print("address = ", i, file=sys.stderr)

        

        # print("IP=", ip_address, file=sys.stderr)
        # print("Forward=", Forward, file=sys.stderr)
        # print("hope=", hope, file=sys.stderr)
        # print("Please work im begging=", sanity, file=sys.stderr)

        # return 
    





    # def ip_handler():


    #     # Configuring a storage backend
        

    #     # Grab the IP
    #     


    #     # Check if more than 50 requests within a 10 second period

    #         # if there has been then block IP for 30 seconds and respond with a 429
            
        
    
        



    return app, socketio




# Start development web server
if __name__ == '__main__':
    app, socketio = create_app()
    
    socketio.run(app, port=8080, host='0.0.0.0', debug=True, allow_unsafe_werkzeug=True)
    

     

    

    

