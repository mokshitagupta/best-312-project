from pymongo import MongoClient
import json, bcrypt

item_1 = {
  "_id" : 1,
  "feature" : "increment",
  "count": 2,
}


def getDB():
    CONNECTION_STRING = "mongodb+srv://max:lqfQqU0nP22yK9LI@cluster0.0gehlmn.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient('localhost')
    # client = MongoClient('mongo') 

    return client['example']



def dbInsert(entry):
    dbname = getDB()
    collection_name = dbname["user_1_items"]
    collection_name.insert_one(entry)

def dbExist(key, value, find, all=True):
    entries = dbQuery(key, value, raw=True, all=all)
    print(entries)
    found = False
    ret = {}

    # #print("Hear are the results: ", entries)
    for e in entries:
        if find in e:
            found = True
            ret = e
            break
    return found, ret

def getUserEntry(key, value, find, all=True):
    entries = dbQuery(key, value, raw=True, all=all)
    print(entries)
    found = False
    ret = {}

    # #print("Hear are the results: ", entries)
    for e in entries:
        if e["username"] == find:
            found = True
            ret = e
            break
    return found, ret

#raw parameter decides if the json blob is returned
def dbQuery(key, val, all=True, raw=False):
    dbname = getDB()
    collection_name = dbname["user_1_items"]
    item_details = [ _ for _ in collection_name.find({key: val})]
    # #print("********ITEMS:  ",[x for x in item_details])
    if all:
        if not raw:
            return json.dumps(item_details)
        else:
            return item_details
    else: 
        if(len(item_details) > 0):
            if raw:
                return [x for x in item_details][0]
            return json.dumps([x for x in item_details][0])
        else:
            return []


# VALID_IMAGES = dbQuery(key="feature", val="img_count", all=False, raw=True)["count"]

def increment(img=False):
    dbname = getDB()
    collection_name = dbname["user_1_items"]
    ctrl = "increment"
    item = item_1
    if img: 
        img_1 = {
            "_id" : increment(),
            "feature" : "img_count",
            "count": 0,
        }
        ctrl = "img_count"
        item = img_1
    key = {"feature" : ctrl}
#    collection_name.insert_one(item_1)
    item_details = [_ for _ in collection_name.find(key)]

    if len(item_details) == 0:
        dbInsert(item)
        return 2
    
    c = item_details[0]["count"]
    n = c + 1
    collection_name.update_one(key,{"$set":{"count":n}})
    #print("INCREMENT COUNT IS ============", n)
    # global VALID_IMAGES
    # VALID_IMAGES = n
    return n


def dbUpdate(val, new):
    dbname = getDB()
    collection_name = dbname["user_1_items"]

    if len([_ for _ in collection_name.find({"_id": val})]) > 0:
        collection_name.update_one({"_id": val},{"$set":new})
        item_details = collection_name.find({"_id": val})
        return json.dumps([x for x in item_details][0])
    
    return None

def dbDelete(val):
    dbname = getDB()
    collection_name = dbname["user_1_items"]

    if len([_ for _ in collection_name.find({"_id": val})]) > 0:
        collection_name.delete_one({"_id": val})
        return True
    
    return False

def dbClean():
    dbname = getDB()
    collection_name = dbname["user_1_items"]
    collection_name.delete_many({"feature":"sessionToken"})
    # collection_name.delete_many({"feature":"img_count"})
    increment(img=True)

    
# dbClean()


def getSalt():
    salt = dbQuery("feature", "salt", all=False, raw=True)
    s = ""
    if salt == []:
        salt = dbQuery("feature", "salt", all=False, raw=True)

        stringer = "";
        if salt == []:
        #generate and insert a salt
            s = bcrypt.gensalt()
            entry = {
                "_id" : increment(),
                "feature" : "salt",
                "salt" : s
            }
        dbInsert(entry)
    else:
        s = salt["salt"]

    return s


def insertSessionId(hash, username):
    entry = {
        "_id" : increment(),
        "username":username,
        "feature":"sessionToken",
        "hash":hash
    }

    dbInsert(entry)