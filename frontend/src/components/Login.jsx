import React from "react";
import '../App.css';

import PreloginNavbar from "./PreloginNavbar";


function validateLogin(email,username,password){

    const pattern = new RegExp("^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$")
    //Minimum eight characters, at least one letter and one number
    //https://stackoverflow.com/questions/19605150/regex-for-password-must-contain-at-least-eight-characters-at-least-one-number-a



    if (email.length == 0 && username.length == 0 ){
        return ["Enter either your email or username to log in", false]
        //some feedback on empty fields
    }


    if (password.length == 0){
        return ["Password field is empty", false]
        //some feedback on empty fields
    }

    return ["", true]
}

function login(){
    const data = new FormData(document.getElementById("login-form"))
    const email = data.get("email")
    const username = data.get("username")
    const password = data.get("password")

    const feedback = validateLogin(email, username, password)

    if ( feedback[1] == false){
        document.getElementById("login-help").innerText = feedback[0]
        return 
    }

    fetch("http://localhost:3008/login", {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        // mode: "cors", // no-cors, *cors, same-origin
        cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
        // credentials: "same-origin", // include, *same-origin, omit
        headers: {
            'Access-Control-Allow-Origin' : "http://localhost:3000",
        //   "Content-Type": "multipart/form-data",
          // 'Content-Type': 'application/x-www-form-urlencoded',
        },
        redirect: "follow", // manual, *follow, error
        referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: data, // body data type must match "Content-Type" header
      })
      .then(
        (res) => {
            console.log(res)
            res.json()
            .then(
                data => document.getElementById("login-help").innerText = data.msg
            )
            
        }
      )
      .catch(
        error => {
            console.log(error)
        }
      )
    

}



export default function Login(){
    return(
        <div class="fixed">
            <PreloginNavbar highlight="login"/>
            <div class="flex-banner">
                <div class="form">
                    <form enctype="multipart/form-data" id="login-form" action="http://localhost:3008/login" method="POST">

                    <span class="">Username:</span> <br></br><br></br>
                        <input class="" type="text" name="username"></input> 
                        <h3>or</h3>

                        <span class="">Email:</span> <br></br><br></br>
                        <input class="" type="text" name="email"></input><br></br><br></br>
                        
                        <span class="">Password:</span> <br></br><br></br>
                        <input class="" type="password" name="password"></input> <br></br>
                        <br></br><br></br> <br></br>
                        <button class="button right" onClick={login} type="button">Login</button>

                        <p id="login-help"></p>

                       
                    </form>
                    

                </div>
            </div>
        </div>
    )
}