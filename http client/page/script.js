/*  --------------
        LINALG
    -------------- */

// point • matrix
function matrixDotVector(matrix, point) {
    // Give a simple variable name to each part of the matrix, a column and row number
    let c0r0 = matrix[0], c1r0 = matrix[1], c2r0 = matrix[2], c3r0 = matrix[3];
    let c0r1 = matrix[4], c1r1 = matrix[5], c2r1 = matrix[6], c3r1 = matrix[7];
    let c0r2 = matrix[8], c1r2 = matrix[9], c2r2 = matrix[10], c3r2 = matrix[11];
    let c0r3 = matrix[12], c1r3 = matrix[13], c2r3 = matrix[14], c3r3 = matrix[15];

    // Now set some simple names for the point
    let x = point[0];
    let y = point[1];
    let z = point[2];
    let w = point[3];

    // Multiply the point against each part of the 1st column, then add together
    let resultX = (x * c0r0) + (y * c0r1) + (z * c0r2) + (w * c0r3);

    // Multiply the point against each part of the 2nd column, then add together
    let resultY = (x * c1r0) + (y * c1r1) + (z * c1r2) + (w * c1r3);

    // Multiply the point against each part of the 3rd column, then add together
    let resultZ = (x * c2r0) + (y * c2r1) + (z * c2r2) + (w * c2r3);

    // Multiply the point against each part of the 4th column, then add together
    let resultW = (x * c3r0) + (y * c3r1) + (z * c3r2) + (w * c3r3);

    return [resultX, resultY, resultZ, resultW];
}

//matrixB • matrixA
function matrixDotMatrix(matrixA, matrixB) {
    // Slice the second matrix up into rows
    let row0 = [matrixB[0], matrixB[1], matrixB[2], matrixB[3]];
    let row1 = [matrixB[4], matrixB[5], matrixB[6], matrixB[7]];
    let row2 = [matrixB[8], matrixB[9], matrixB[10], matrixB[11]];
    let row3 = [matrixB[12], matrixB[13], matrixB[14], matrixB[15]];

    // Multiply each row by matrixA
    let result0 = matrixDotVector(matrixA, row0);
    let result1 = matrixDotVector(matrixA, row1);
    let result2 = matrixDotVector(matrixA, row2);
    let result3 = matrixDotVector(matrixA, row3);

    // Turn the result rows back into a single matrix
    return [
        result0[0], result0[1], result0[2], result0[3],
        result1[0], result1[1], result1[2], result1[3],
        result2[0], result2[1], result2[2], result2[3],
        result3[0], result3[1], result3[2], result3[3]
    ];
}


/*  -----------
        GUI
    ----------- */

inputConnectionHost = document.getElementById("input-connection-host");
function getHost() {
    return inputConnectionHost.value;
}
inputConnectionPort = document.getElementById("input-connection-port");
function getPort() {
    return inputConnectionPort.value;
}
inputConnectionClientName = document.getElementById("input-connection-client-name");
function getName() {
    return inputConnectionClientName.value;
}

outputConnectionStatus = document.getElementById("output-connection-status");
function displayConnectionStatus(status) {
    outputConnectionStatus.innerHTML = status;
}
outputIsControlling = document.getElementById("output-is-controlling");
function displayIsControlling(value) {
    outputIsControlling.checked = value;
}
outputIsLogging = document.getElementById("output-is-logging");
function displayIsLogging(value) {
    outputIsLogging.checked = value;
}
outputVector = document.getElementById("output-vector");
function displayVector(t, vector) {
    outputVector.innerHTML = "t: "+Math.round(t*100)/100+"s ["+vector+"]";    
}
outputCurrentTime = document.getElementById("output-current-time");
function displayCurrentTime(value) {
    outputCurrentTime.innerHTML = Math.round(value*100)/100 + "s";
}

inputControlX = document.getElementById("input-control-x");
inputControlY = document.getElementById("input-control-y");
inputControlZ = document.getElementById("input-control-z");
function getInputCoordinates() {
    return [parseFloat(inputControlX.value), parseFloat(inputControlY.value), parseFloat(inputControlZ.value)];
}

inputControlTeta1 = document.getElementById("input-control-teta1");
inputControlTeta2 = document.getElementById("input-control-teta2");
inputControlTeta3 = document.getElementById("input-control-teta3");
function getInputAngles() {
    return [parseFloat(inputControlTeta1.value), parseFloat(inputControlTeta2.value), parseFloat(inputControlTeta3.value)].map(function(x) { return x * Math.PI / 180; });;
}

/*  --------------
        AFRAME
    -------------- */

var robotParts = [];
var robotAxes = [];
for (var i = 0; i <= 2; ++i) {
    robotParts[i] = document.getElementById("robot-part"+(i+1));
    robotAxes[i] = document.getElementById("robot-axes"+(i+1));
}

function setupManipulator(sizes) {
    // TODO change size of manipulator model
}

function displayManipulatorAngles(vector) {
    robotAxes[0].object3D.rotation.y = -vector[0];
    robotAxes[1].object3D.rotation.z = -vector[1];
    robotAxes[2].object3D.rotation.z = -vector[2];
}

/*  --------------
        OTHERS
    -------------- */

var socket;
var isRegistered = false;

var lastVectorT = 0.0;
var lastVector = [0, 0, 0];
var sizes = [1, 1, 1];

var isLogging = false;
var isControlling = false;

var startTime = Date.now() / 1000;

function coordsToAngles(sizes, coords) {
    pi = Math.PI;
    a1 = sizes[0];
    a2 = sizes[1];
    a3 = sizes[2];
    x = coords[0];
    y = coords[1];
    z = coords[2];
    x31 = Math.sqrt(x*x+z*z);
    teta1 = Math.atan2(z, x);
    y31 = y - a1;
    teta3 = pi - Math.acos((a2*a2+a3*a3-x31*x31-y31*y31)/(2*a2*a3));
    teta2 = pi/2 - Math.acos((a2*a2+y31*y31+x31*x31-a3*a3)/(2*a2*Math.sqrt(x31*x31+y31*y31))) - Math.atan2(y31, x31);
    return [teta1, teta2, teta3];
}

function anglesToCoords(sizes, tetas) {
    teta1 = tetas[0];
    teta2 = tetas[1];
    teta3 = tetas[2];
    a1 = sizes[0];
    a2 = sizes[1];
    a3 = sizes[2];
    // ! matrix inputs column by column
    T10 = [Math.cos(teta1), 0, Math.sin(teta1), 0, 0, 1, 0, 0, -Math.sin(teta1), 0, Math.cos(teta1), 0, 0, a1, 0, 1];
    T21 = [Math.cos(teta2), -Math.sin(teta2), 0, 0, Math.sin(teta2), Math.cos(teta2), 0, 0, 0, 0, 1, 0, a2*Math.sin(teta2), a2*Math.cos(teta2), 0, 1];
    T32 = [Math.cos(teta3), -Math.sin(teta3), 0, 0, Math.sin(teta3), Math.cos(teta3), 0, 0, 0, 0, 1, 0, a3*Math.sin(teta3), a3*Math.cos(teta3), 0, 1];
    // ! vector is one matrix column
    k3 = [0, 0, 0, 1];
    k0 = matrixDotMatrix(T10, matrixDotMatrix(T21, matrixDotVector(T32, k3)));
    return [k0[0], k0[1], k0[2]];
}

function getCurrentTime() {
    return Date.now() / 1000 - startTime;
}

function showConnectionStatus() {
    switch (socket.readyState) {
        case WebSocket.CONNECTING:
            displayConnectionStatus("connecting");
            break;
        case WebSocket.OPEN:
            displayConnectionStatus("opened");
            break;
        case WebSocket.CLOSING:
            displayConnectionStatus("closing");
            break;
        case WebSocket.CLOSED:
            displayConnectionStatus("closed");
            break;
        default:
            break;
    }
}

function connectWebsocket(url) {
    socket = new WebSocket(url);
    socket.onopen = socketOpeningEvent;
    socket.onclose = socketCloseEvent;
    socket.onmessage = socketMessageEvent;
    socket.onerror = socketErrorEvent;
    showConnectionStatus();
    isRegistered = false;
}

function sendWebsocket(msg) {
    if (socket.readyState == WebSocket.OPEN) {
        console.log("Me: "+JSON.stringify(msg));
        socket.send(JSON.stringify(msg));
    }
}

function registerClient() {
    req = {"type": "connect", "vector_format": ["teta1", "teta2", "teta3"], "coefficients_format": ["kp", "ki", "kd"], "name": getName()};
    sendWebsocket(req);
}

function sendVector(t, vector) {
    req = {"type": "vector", "t": t, "vector": vector};
    sendWebsocket(req);
}

function clear() {
    lastVectorT = 0;
    lastVector = [0, 0, 0];
    displayVector(lastVectorT, lastVector);
    displayManipulatorAngles(lastVector);
    startTime = Date.now() / 1000;
}

function interpretServer(msg) {
    messageType = msg.type;
    switch (messageType) {
        case "connect_answer":
            if (msg.code != 0) {
                // TODO something went wrong; describe it
                socket.close(1000);
            }
            break;
        case "vector":
            lastVectorT = msg.t;
            lastVector = msg.vector;
            displayVector(Math.round(lastVectorT*100)/100, lastVector);
            displayManipulatorAngles(lastVector);
            break;
        case "set_logging":
            isLogging = msg.value == 1;
            displayIsLogging(isLogging);
            break;
        case "set_controlling":
            isControlling = msg.value == 1;
            displayIsControlling(isControlling);
            break;
        case "clear":
            clear();
            break;
        case "set_coefficients":
            // TODO ???
            break;
        default:
            break;
    }
}

function initAll() {
    
}

/*  --------------
        EVENTS
    -------------- */

function socketOpeningEvent(e) {
    console.log("[New connection]");
    showConnectionStatus();
    if (!isRegistered) {
        isRegistered = true;
        registerClient();
    }
}

function socketMessageEvent(e) {
    msg = JSON.parse(e.data);
    console.log("Server: "+JSON.stringify(msg));
    interpretServer(msg);
}

function socketCloseEvent(e) {
    console.log("[Connection closed]");
    showConnectionStatus();
}

function socketErrorEvent(e) {
    console.log("[Connection failed]");
    showConnectionStatus();
}

function eventButtonConnection() {
    if (socket) {
        socket.close(1000);
    }
    var url = "ws://"+getHost()+":"+getPort();
    connectWebsocket(url);
}

function eventButtonSendCoordinates() {
    coords = getInputCoordinates();
    tetas = coordsToAngles(sizes, coords);
    t = getCurrentTime();
    sendVector(t, tetas);
    lastVectorT = t;
    lastVector = tetas;
    displayVector(lastVectorT, lastVector);
    displayManipulatorAngles(lastVector);
}

function eventButtonSendAngles() {
    tetas = getInputAngles();
    t = getCurrentTime();
    sendVector(t, tetas);
    lastVectorT = t;
    lastVector = tetas;
    displayVector(lastVectorT, lastVector);
    displayManipulatorAngles(lastVector);
}

function eventUpdateTime() {
    displayCurrentTime(getCurrentTime());
}
setInterval(eventUpdateTime, 100);