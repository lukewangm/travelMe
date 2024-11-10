// const WebSocket = require('ws');
// const server = new WebSocket.Server({ port: 3000 });

// var timerEndTimes = [null, null, null, null];
// var clientMessageHistory = new Map(); // Tracks messages sent to each client

// const sendCurrentTime = () => {
//     timerEndTimes.forEach((endTime, i) => {
//         if (endTime !== null) {
//             const timerMsg = {
//                 id: i,
//                 endTime: endTime,
//                 reset: false,
//             };
//             server.clients.forEach((client) => {
//                 if (client.readyState === WebSocket.OPEN) {
//                     client.send(JSON.stringify(timerMsg));
//                 }
//             });
//         }
//     });
// };

// server.on('connection', (socket) => {
//     socket.on('message', (message) => {
//         try {
//             const timerMsg = JSON.parse(message);

//             if (timerMsg.type === "requestTimer") {
//                 sendCurrentTime();
//             } else {
//                 console.log('Received timer:', timerMsg.id);
//                 timerEndTimes[timerMsg.id] = timerMsg.endTime;
//                 console.log(timerEndTimes[timerMsg.id]);
//                 server.clients.forEach((client) => {
//                     if (client !== socket && client.readyState === WebSocket.OPEN) {
//                         client.send(message);
//                     }
//                 });
//             }
//         } catch (e) {
//             console.error("Failed to parse incoming message as JSON:", e);
//         }
//     });
// });


const WebSocket = require('ws');
const server = new WebSocket.Server({ port: 3000 });
const { v4: uuidv4 } = require('uuid');

var timerEndTimes = [null, null, null, null];
var clientMessageHistory = new Map(); // Tracks messages sent to each client

const sendCurrentTime = () => {
    timerEndTimes.forEach((endTime, i) => {
        if (endTime !== null) {
            const timerMsg = {
                id: i,
                endTime: endTime,
                reset: false,
            };
            server.clients.forEach((client) => {
                if (client.readyState === WebSocket.OPEN) {
                    // Assuming each client has a unique clientId property
                    const clientId = client.clientId;
                    const history = clientMessageHistory.get(clientId) || [];

                    // Check if this message has already been sent to this client
                    if (!history.includes(timerMsg.id)) {
                        client.send(JSON.stringify(timerMsg));
                        // Update the history
                        history.push(timerMsg.id);
                        clientMessageHistory.set(clientId, history);
                    }
                }
            });
        }
    });
};

server.on('connection', (socket, req) => {
    // Generate or obtain a unique ID for each client
    const clientId = generateOrObtainClientId(req);
    socket.clientId = clientId; // Attach clientId to the socket
    console.log(`Client connected with ID: ${clientId}`);

    socket.on('message', (message) => {
        try {
            const timerMsg = JSON.parse(message);

            if (timerMsg.type === "requestTimer") {
                sendCurrentTime();
            } else {
                console.log('Received timer:', timerMsg.id);
                timerEndTimes[timerMsg.id] = timerMsg.endTime;
                console.log(timerEndTimes[timerMsg.id]);

                // Send update to all clients except the sender
                server.clients.forEach((client) => {
                    if (client !== socket && client.readyState === WebSocket.OPEN) {
                        const history = clientMessageHistory.get(client.clientId) || [];
                        if (!history.includes(timerMsg.id)) {
                            client.send(message);
                            history.push(timerMsg.id);
                            clientMessageHistory.set(client.clientId, history);
                        }
                    }
                });
            }
        } catch (e) {
            console.error("Failed to parse incoming message as JSON:", e);
        }
    });
});

function generateOrObtainClientId(req) {
    // Generate a new UUID as the clientId
    const clientId = uuidv4();
    return clientId;
}
