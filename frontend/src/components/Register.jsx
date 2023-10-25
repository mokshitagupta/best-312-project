import React from "react";
import '../App.css';

import PreloginNavbar from "./PreloginNavbar";


function validatePassword(email,username,password,confPassword){

    const pattern = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/
    const usernamePattern = /^[a-zA-Z0-9]+$/
    const emailPattern = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|.(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    
    //Minimum eight characters, at least one letter and one number
    //https://stackoverflow.com/questions/19605150/regex-for-password-must-contain-at-least-eight-characters-at-least-one-number-a
    //https://stackoverflow.com/questions/46155/how-can-i-validate-an-email-address-in-javascript



    if (email.length == 0 ){
        return ["Email field is empty", false]
        //some feedback on empty fields
    }

    if ( username.length == 0 ){
        return ["Username field is empty", false]
        //some feedback on empty fields
    }

    if (password.length == 0){
        return ["Password field is empty", false]
        //some feedback on empty fields
    }

    if (confPassword.length == 0){
        return ["Confirm Password is empty", false]
        //some feedback on empty fields
    }

    console.log(pattern.test(password))

    if (pattern.test(password) == false){
        return ["Password must contain minimum eight characters, at least one letter and one number", false]
        //some feedback on weak pass
    }

    if (usernamePattern.test(username) == false){
        return ["Username is invalid", false]
        //some feedback on weak pass
    }

    if (emailPattern.test(email) == false){
        return ["Wmail is invalid", false]
        //some feedback on weak pass
    }

    if (password != confPassword){
        return ["Passwords doesn't match", false]
        //some feedback on different pass
    }

    return ["", true]
}

function displayFeedback(id, feed){
    document.getElementById(id).innerText = feed
}

function register(){
    const data = new FormData(document.getElementById("register-form"))
    const email = data.get("email")
    const username = data.get("username")
    const password = data.get("password")
    const confPassword = data.get("confPassword")

    const feedback = validatePassword(email, username, password, confPassword)

    if ( feedback[1] == false){
        displayFeedback("reg-help", feedback[0])
        return 
    }

    fetch("http://localhost:3008/register", {
        method: "POST",
        credentials: 'include',
        body: data, 
      })
      .then(
        (res) => {
            res.json()
            .then(data => displayFeedback("reg-help",data.msg))
        }
      )
      .catch(
        error => {
            console.log(error)
        }
      )
    

}



export default function Register(){
    return(
        <div class="fixed">
            <PreloginNavbar highlight="register"/>
            <div class="flex-banner">
                
                <div class="reg-form">
                    <form id="register-form">
                        <span class="">Email:</span> <br></br><br></br>
                        <input class="" type="text" name="email"></input> <br></br>                        
                        <br></br>
                        
                        <span class="">Username:</span> <br></br><br></br>
                        <input class="" type="text" name="username"></input> <br></br><br></br>
                        <span class="">Password:</span> <br></br><br></br>
                        <input class="" type="password" name="password"></input> <br></br><br></br>
                        <span class="">Confirm Password:</span> <br></br><br></br>
                        <input class="" type="password" name="confPassword"></input> <br></br>
                        <p>Passwords must contain 8 characters, with at least 1 number and letter</p>
                        <br></br>
                        

                        <p id="reg-help"></p>
                        
                        <br></br>
                        
                
                    </form>

                    <button onClick={register} class="button right">Register</button>

                </div>

            </div>
        </div>
    )
}