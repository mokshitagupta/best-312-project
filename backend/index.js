const express = require('express')
var bodyParser = require('body-parser');
var multer = require('multer');
var upload = multer();
var app = express();

const db =  require('./db.js')
const bcrypt = require("bcrypt")

const saltRounds = 10

var cors = require('cors')

app.use(cors())

const port = 3008

app.use(bodyParser.json()); 

// for parsing application/xwww-
app.use(express.urlencoded({ extended: true }))
//form-urlencoded

// for parsing multipart/form-data
app.use(upload.array()); 


var cookieParser = require('cookie-parser');
app.use(cookieParser());

function createAuthToken(length, user){
  let choices = "abcdefgehijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  let ret = ""

  for(let i=0; i < length ; i++){
    let char = Math.floor(Math.random() * choices.length)
    ret += char.toString()
  }

  entry = {
    path :"/tokens",
    token:ret,
    user: user, 
  }

  db.dbInsert(entry)

  return ret
}

function handleLogin(req, res){
  console.log(req.body)
  const email = req.body.email
  const username = req.body.username
  const password = req.body.password


  if ((email && email.length>0) || (username && username.length>0)){

    console.log("starting")
    db.dbFind("email", email)
    .then((queryEmail) => {
      if (queryEmail) {
        bcrypt.compare(password, queryEmail.password)
        .then((result) => {
          console.log("result of pass comp: ", result)
          if (result == true){
            let token = createAuthToken(length=8, user=myID)

            console.log(token, entry, "YOUR TOKEN")

            res.cookie('token', token, {maxAge: 24 * 60 * 60 * 1000, httpOnly: true}) // 24 hours
            res.cookie('id', myID, {maxAge: 24 * 60 * 60 * 1000, httpOnly: true})

            res.send(JSON.stringify({userID:myID,token: token,success:true, msg:'Login Successful!'}))
            return true
          }else {
            res.status(401).send(JSON.stringify({success:false, msg:'Incorrect password'}))
            return true
          }
        })
      }else{
        return false
      }
      
    })
    .then(valid => {
      if( valid == true){
        return true
      }
      if (username && username.length>0){
        db.dbFind("username", username)
        .then((queryEmail) => {
          if (queryEmail ) {
            bcrypt.compare(password, queryEmail.password)
            .then((result) => {
              console.log("result of pass comp: ", result)
              if (result == true){
                let token = createAuthToken(length=8, user=myID)

                console.log(token, entry, "YOUR TOKEN")

                res.cookie('token', token, {maxAge: 24 * 60 * 60 * 1000, httpOnly: true}) // 24 hours
                res.cookie('id', myID, {maxAge: 24 * 60 * 60 * 1000, httpOnly: true})

                res.send(JSON.stringify({userID:myID,token: token,success:true, msg:'Login Successful!'}))
                
                return true
              }else {
                res.status(401).send(JSON.stringify({success:false, msg:'Incorrect password'}))
                return true
              }
            })
          }else{
            res.status(401).send(JSON.stringify({success:false, msg:'Email or password not found...'}))
          }
        })
        .catch((err) => console.log(err))
      }


    })

  }

}

function handleRegister(req, res){
  console.log(req.body)
  const email = req.body.email
  const username = req.body.username
  const password = req.body.password

  let valid = true

  db.dbFind("email", email)
  .then((queryEmail) => {
    // console.log("found ---> ",queryEmail.length)
    if (queryEmail) {
      valid = false
      res.status(400).send(JSON.stringify({success:false, msg:'Email is already taken'}))
      return valid
    }

    return valid
  })
  .then((valid) => {
    if (valid == false){
      return false
    }

    db.dbFind("username", username)
    .then((queryUser) => {
    if (queryUser) {
      valid = false
      res.status(400).send(JSON.stringify({success:false, msg:'Username is already taken'}))
      return valid
    }})

    return valid

  })
  .then((valid) => {
    if (valid == false){
      return
    }

    const entry = {
      username:username,
      email:email,
      password:password,
      path:"/users",
    }
  
    db.increment()
    .then((myID) => {
  
      bcrypt.genSalt(saltRounds)
      .then((salt) => {
        return bcrypt.hash(req.body.password, salt)
      })
      .then((hash) => {
  
        entry._id = myID
        entry.password = hash
  
        db.dbInsert(entry)
        .then(() => {
          console.log("inserted: ", entry)

          let token = createAuthToken(length=8, user=myID)

          console.log(token, entry, "YOUR TOKEN")

          res.cookie('token', token, {maxAge: 24 * 60 * 60 * 1000}) // 24 hours
          res.cookie('id', myID, {maxAge: 24 * 60 * 60 * 1000}) 
          res.send(JSON.stringify({userID:myID,token: token,success:true, msg:'Registration was successful!!'}))
          // res.send(JSON.stringify({success:true, id:entry._id, msg:'Registration was successful!'}))
        })
        .catch((err) => console.log(err))
  
      })
    })
    .catch((err) => console.log(err))
  })
}

app.post('/login', handleLogin)

app.post('/register', handleRegister)


app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})