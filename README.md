### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

This starts an client that can pings against my AWS EC2 instance, the public ip is: 'ws://34.226.198.62:3000'.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

### `node src/server.js`

Starts the server locally, but the web sockets need be changed to reflect where the server is. 

This code is currently intended to run on your machine locally. Line 8 in MyTimer.jsx can be changed to reflect where the server is, so web sockets can connect.