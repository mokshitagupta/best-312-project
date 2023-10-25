const { MongoClient } = require('mongodb');

async function getDB(){
    const client = new MongoClient("mongodb://localhost:27017/MyDb");
    let conn;
    try {
    conn = await client.connect();
    } catch(e) {
    console.error(e);
    }

    let db = conn.db("some_app");
    return db
}

function dbInsert(entry){
    return getDB().then(async (db) => {
        let collection = await db.collection("some_game");
        let result = await collection.insertOne(entry)
        // let result = await collection.find({}).toArray()
        console.log(result)
        return result
    })
}

function dbFind(fkey, value){
    return getDB().then(async (db) => {

        let collection = await db.collection("some_game");
        console.log(fkey, value)

        await collection.find({}).toArray()
        // .then( (result) => {console.log(result)
        // return result})

        return await collection.findOne({[fkey]:value})
        .then( (result) => {console.log(result)
        return result})
        // return result
    })
}

function dbUpdate(key,value,nkey,nvalue){
    return getDB().then(async (db) => {

        let collection = await db.collection("some_game");
        // console.log(fkey, value)
        await collection.updateOne({[key]:value}, {$set:{[nkey]:nvalue}})
        .then( (result) => {console.log("update --- ",result)
        return result})
        // return result
    })
}

function increment(){
    return getDB().then(async (db) => {

        let collection = await db.collection("some_game");
        return await collection.findOne({feature:"increment"})
        .then( (result) => {
            console.log(result)
            if (!result){

                entry = {
                    feature:"increment",
                    count:2,
                }

                dbInsert(entry)

                return 1
                //insert new into db
            }
            // update db val and return old
            dbUpdate("feature", "increment","count", result.count+1)
            return result.count
        }
        )
        // return result
    })
}
// await client.connect();

module.exports = {
    dbInsert,
    dbFind,
    increment,
    dbUpdate,
}