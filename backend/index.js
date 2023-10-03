
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

function handleLogin(req, res){
  console.log(req.body)
  const email = req.body.email
  const username = req.body.username
  const password = req.body.password


  if (email && email.length>0 || username && username.length>0){
    db.dbFind("email", email)
    .then((queryEmail) => {
      if (queryEmail && queryEmail.length > 0) {
        bcrypt.compare(password, queryEmail.password)
        .then((result) => {
          if (result == true){
            res.send(JSON.stringify({success:true, msg:'Login Successful!'}))
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
              if (result == true){
                res.send(JSON.stringify({success:true, msg:'Login Successful!'}))
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
          if (valid == false){
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
          res.send(JSON.stringify({success:true, id:entry._id, msg:'Registration was successful!'}))
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