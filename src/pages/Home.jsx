import React from "react";
import {useNavigate} from "react-router-dom";

function Home() {
    const navigate = useNavigate();
    return (
        <div>
            <h1>Home</h1>
            {/* <button onClick={() => navigate("/Messages")}>Go to Messages</button> */}
            <button onClick={() => navigate("/Timers")}>Go to Timers</button>
            <button onClick={() => navigate("/Messages")}>Go to Messages</button>
        </div>

    )
}

export default Home;