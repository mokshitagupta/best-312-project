
import './App.css';
import React from "react";

import Homepage from './components/Homepage.jsx';
import Register from './components/Register.jsx';
import Login from './components/Login.jsx';
// import SetupAccount from './components/SetupAccount.jsx';

import { BrowserRouter, Route, Routes } from "react-router-dom";


function App() {
  // console.log(process.env.REACT_APP_BASE_URL)
  return (
    <div className="App">
      <header className="App-header">
      </header>
        <BrowserRouter basename={process.env.REACT_APP_BASE_URL}>
        <Routes>
          {/* <Route path="/setup-account" element={<SetupAccount />} /> */}
           <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} /> 
          <Route path="/" element={<Homepage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;