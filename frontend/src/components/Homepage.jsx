// import React from "react";
import '../App.css';

import PreloginNavbar from "./PreloginNavbar.jsx";

// import banner from "./assets/banner.png"

function Homepage(){
    return (
        <div>
            <PreloginNavbar/> 

                <div id="hp-flex">
                {/* <img src={banner} id="banner"></img> */}
                <div id="intro-text">
                    <p>{"something about how amazing we are ... <3"} </p>
                </div> 
            </div> 
        </div>
    )
}

export default Homepage