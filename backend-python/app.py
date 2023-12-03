import json

from flask import Flask, flash, render_template_string, session, render_template, request, Response, make_response, redirect, url_for, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from pymongo import MongoClient
import webbrowser

import bcrypt, random, html, os
from db import *
import datetime
from google_auth_oauthlib.flow import Flow
import google_auth_oauthlib.flow
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
import google.auth
import os, sys
import random, string

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
webbrowser.register('chrome', None, webbrowser.GenericBrowser('/Applications/Google\ Chrome.app %s'))


class ConfigClass(object):
    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'


def save_credentials(credentials):
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def load_credentials():
    if 'credentials' in session:
        creds = google.oauth2.credentials.Credentials(**session['credentials'])
        return creds
    return None


def generateLink(email):
    base = "https://bidbig.live/verify-account?emailverif="
    token = "".join(random.choices(string.ascii_uppercase + string.digits, k=85))

    exists, userinfo = getEmailEntry("path", "email-verif", email, all=True)

    if exists:
        base = base + userinfo["token"] + "&id="+ str(userinfo["_id"])
        return base

    entry = {
        "_id": increment(),
        "path": "email-verif",
        "token":token,
        "email":email,
        "verified":False,
    }

    base = base+token + "&id="+ str(entry["_id"])

    dbInsert(entry)
    print(base+token)
    return base

def print_info(request):
    for i in request.headers:
        print("header = ", i, file=sys.stderr)
    for i in request.environ:
        print("enviorn = ", i, file=sys.stderr)
    print("address = ", request.remote_addr, file=sys.stderr)
    print("REMOTE_ADDR = ", request.environ.get("REMOTE_ADDR"), file=sys.stderr)
    print("address = ", request.remote_addr, file=sys.stderr)

def create_app():
    # Setup Flask and load app.config
    app = Flask(__name__)
    app.config.from_object(__name__ + '.ConfigClass')
    socketio = SocketIO(app)
    socketio.init_app(app, cors_allowed_origins="*")

    @socketio.on('time')
    def handle_message(data):
        id = data["id"]
        entry = dbQuery("_id", id, all=False, raw=True)
        print("print")

        #this is probably where the post auction clean up code will need to be added for LO3
        if len(entry) > 0:
            rem =  datetime.datetime.strptime(entry["duration"], "%m/%d/%Y %H:%M:%S") - datetime.datetime.now()
            retTime = int(rem.total_seconds())
            if retTime < 0:
                dbUpdate(id, {"active":False})
                dbUpdate(id, {"finalWinner": entry["winner"]})
            return retTime
        else:
            return -1
    
    @socketio.on('hello_world')
    def hello_world_test(data):
        print(f'Recieved from client: {data}')
        return 'Hello World from Server!!'
    
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


                    
                elif bid > entry["highestBid"] and entry["username"]!=userinfo["username"]:
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
            print(exists, entry, query[0]["username"])

            verified, _ =  getUserEntry("path", "verified", entry["username"], all=True)
            print(entry["username"], verified, "<======= verif status")
            if verified:
                return render_template('comments.html', username=entry["username"], username_hidden=entry["username"],
                                       verif_status='Your email was verified!',
                                       verif_link="",
                                       verify_text="")
            else:
                return render_template('comments.html', username=entry["username"], username_hidden=entry["username"],
                                       verif_status='Verify your email here:',
                                       verif_link=url_for("oauth2callback1"),
                                       verify_text="Verify!")
        
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
                "finalWinner": "N/A (Auction still active)",
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

    @app.route('/verify-account')
    def verifemail():
        token = request.args.get('emailverif')
        eid = request.args.get('id')

        exists, entry = getEmailTokenEntry("path", "email-verif", token, all=True)
        print("INFO =========>>> ",exists, entry,eid)

        if exists:
            # print(dbUpdate( eid, {"verified":True}))

            entry = {
                "_id":increment(),
                "path":"verified",
                "username":entry["email"]
            }

            dbInsert(entry)
            # exists, entry = getEmailTokenEntry("path", "email-verif", token, all=True)
            # print("NEW ------> ", entry)
            return redirect("/")
 
        # print(token)
        return "This link is not valid! Recheck your email for the correct one"
    
    @app.route('/test')
    def oauth2callback1():
        name = request.cookies.get('token')
        entry = {}
        print(name)
        if name == None:
            # no auth token
            return render_template('register.html')

        salted = bcrypt.hashpw(name.encode("utf-8"), getSalt())
        query = dbQuery("hash", salted, raw=True)
        if len(query) == 0:
            return render_template('register.html')

        else:
            exists, entry = getUserEntry("path", "registeredUsers", query[0]["username"], all=True)
            print("INFO =========>>> ",exists, entry)

        credentials = None
        if os.path.exists("auth/token.json"):
            try:
                with open("auth/token.json", "r") as token:
                    print("READ: ", json.load(token))
                credentials = Credentials.from_authorized_user_file("auth/token.json", ['https://www.googleapis.com/auth/gmail.send'])

            except json.decoder.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
            
        if credentials==None or not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
                    "auth/credentials.json", scopes=['https://www.googleapis.com/auth/gmail.send'])

                # The URI created here must exactly match one of the authorized redirect URIs
                # for the OAuth 2.0 client, which you configured in the API Console. If this
                # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
                # error.
                flow.redirect_uri = url_for('oauth2callback', _external=True)

                authorization_url, state = flow.authorization_url(
                    # Enable offline access so that you can refresh an access token without
                    # re-prompting the user for permission. Recommended for web server apps.
                    access_type='offline',
                    # Enable incremental authorization. Recommended as a best practice.
                    include_granted_scopes='true')

                # Store the state so the callback can verify the auth server response.
                session['state'] = state
                print("redir", authorization_url)
                return redirect(authorization_url)

            

        # credentials = service_account.Credentials.from_service_account_file(
        #     'auth/token.json',
        #     scopes=['https://www.googleapis.com/auth/gmail.send']
        # )

        service = build('gmail', 'v1', credentials=credentials)

        link = generateLink(entry["username"])

        message = MIMEText('Go to this link to verify that this is a valid email address: '+link)
        message['to'] = entry["username"]
        print("Sending to: ", message['to'])
        message['from'] = 'bidbig106@gmail.com'
        message['subject'] = 'Your Bid Big Verification Link!'

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send the email
        try:
            message = (service.users().messages().send(userId='me', body={'raw': raw_message}).execute())
            print('Message Id: %s' % message['id'])
            return redirect("/")
        except Exception as e:
            print(f'An error occurred: {e}')
            return 'An error occurred while sending the email.'
        
    @app.route('/oauth2callback')
    def oauth2callback():


        print('here')
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
        state = session['state']

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            "auth/credentials.json", scopes=['https://www.googleapis.com/auth/gmail.send'], state=state)
        flow.redirect_uri = url_for('oauth2callback', _external=True)

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials in the session.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        credentials = flow.credentials
        print(credentials.to_json())
        with open("auth/token.json", "w") as token:
            token.write(credentials.to_json())
        with open("auth/token.json", "r") as token:
            print("WROTE: ", json.load(token))

        


        return redirect(url_for('oauth2callback1'))
            

    return app, socketio




# Start development web server
if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['PYTHONUNBUFFERED'] = '1'

    app, socketio = create_app()
    
    socketio.run(app, port=8080, host='0.0.0.0', debug=True, allow_unsafe_werkzeug=True)
    

     

    

    

