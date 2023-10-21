import React from "react";
import '../App.css';

// import logo from "./assets/logo.png"

function PreloginNavbar(props){
    console.log(props)
    
    let comp = (props.links == false ) 
        ?
        null : 
        <div id="nav-links">
            <a class= {(props.highlight && props.highlight === "login" )? "blue" : "white"} href="/login">Login</a>
            <a class= {(props.highlight && props.highlight === "register" )? "blue" : "white"} href="/register">Register</a>
        </div>

    console.log(comp, ( props.links == false ) )
    return (
        <div id="navbar">
            <a href="/" id="logo"> Homepage
                {/* <img src={logo}></img> */}
            </a>

            
            {comp}
            
        </div>
    )
}

export default PreloginNavbar