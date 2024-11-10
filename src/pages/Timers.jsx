import React from 'react';
import MyTimer from './MyTimer'; // Adjust the import path based on your file structure
import {useNavigate} from "react-router-dom";

const Timers = () => {
    const navigate = useNavigate();
    // style={{margin: "auto", borderStyle: 'dashed', borderColor:'black'}}
    return (
        <div>
            <div id= "row" style={{ backgroundColor: 'beige', margin: "auto"}} >
                    <h1>Laundry-Comms</h1>
                {/* <button onClick={() => navigate("/")}>Go to Home</button> */}
            </div>
            <div id = "row">
                <div id = "timerCard">
                    <h1>Left Room</h1>
                    <hr></hr>
                    <MyTimer timerID = {0} initialMinutes={35} />
                    <MyTimer timerID = {1} initialMinutes={45} />
                </div>
                <div id = "timerCard">
                    <h1>Right Room</h1>
                    <hr></hr>
                    <MyTimer timerID = {2} initialMinutes={35} />
                    <MyTimer timerID = {3} initialMinutes={45} />
                </div>    
            </div>
            
        </div>
    );
};

export default Timers;