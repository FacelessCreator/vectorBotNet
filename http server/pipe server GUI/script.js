
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

outputConnectionStatus = document.getElementById("output-connection-status");
function displayConnectionStatus(status) {
    outputConnectionStatus.innerHTML = status;
}

VRContainer = document.getElementById("VR-container");
menuContainer = document.getElementById("menu-container");

/*  --------------
        AFRAME
    -------------- */

var scene = document.querySelector('a-scene');

class Robot {
    constructor(scene, consts) {

    }
    move(vector) {

    }
    remove() {

    }
}

class Manipulator extends Robot {
    constructor(scene, consts) {
        super(scene, consts);
        this.axes = [];
        this.parts = [];
        this.sizes = [consts.a1, consts.a2, consts.a3];
        for (var i = 0; i < 3; i++) {
            this.axes[i] = document.createElement('a-entity');
            this.parts[i] = document.createElement('a-entity');
            this.parts[i].setAttribute('geometry', {
                primitive: 'box',
                height: this.sizes[i],
                width: 0.05,
                depth: 0.05
            });
            //this.parts[i].setAttribute('material', {color: '#005500'});
            this.parts[i].setAttribute('position', { x: 0, y: (this.sizes[i] / 2.0), z: 0 });
            this.axes[i].appendChild(this.parts[i]);
            if (i > 0) {
                this.axes[i].setAttribute('position', { x: 0, y: (this.sizes[i-1] / 2.0), z: 0 });
                this.parts[i-1].appendChild(this.axes[i]);
            }
        }
        scene.appendChild(this.axes[0]);
    }

    move(vector) {
        this.axes[0].object3D.rotation.y = -vector[3];
        this.axes[1].object3D.rotation.z = -vector[4];
        this.axes[2].object3D.rotation.z = -vector[5];
    }

    remove() {
        scene.removeChild(this.axes[0]);
    }
}

class Segway extends Robot {
    constructor(scene, consts) {
        super(scene, consts);
        this.shape = document.createElement('a-entity');
        this.body = document.createElement('a-entity');
        this.wheelL = document.createElement('a-entity');
        this.wheelR = document.createElement('a-entity');
        this.body.setAttribute('geometry', {primitive: 'box', width: 0.072, height: 0.110, depth: 0.052});
        this.body.setAttribute('position', {x: 0, y: 0.092, z: 0});
        this.wheelL.setAttribute('geometry', {primitive: 'cylinder', height: 0.028, radius: 0.028});
        this.wheelL.setAttribute('position', {x: 0, y: 0, z: 0.092});
        this.wheelL.setAttribute('rotation', {x: 90, y: 0, z: 0});
        this.wheelR.setAttribute('geometry', {primitive: 'cylinder', height: 0.028, radius: 0.028});
        this.wheelR.setAttribute('position', {x: 0, y: 0, z: -0.092});
        this.wheelR.setAttribute('rotation', {x: 90, y: 0, z: 0});
        this.shape.appendChild(this.body);
        this.shape.appendChild(this.wheelL);
        this.shape.appendChild(this.wheelR);
        scene.appendChild(this.shape);
    }

    move(vector) {
        this.shape.object3D.position.x = vector[0];
        this.shape.object3D.position.z = -vector[1];
        this.shape.object3D.rotation.y = vector[2];
        this.shape.object3D.rotation.z = -vector[3];
    }

    remove() {
        scene.removeChild(this.shape);
    }
}

/*  --------------
        OTHERS
    -------------- */

var socket;
var isRegistered = false;

var robots = {};

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
    req = {"type": "connect"};
    sendWebsocket(req);
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
        case "new_client":
            if (!("GUI_format" in msg)) {
                robots[msg.name] = new Robot(scene, null);
            } else {
                consts = msg.GUI_format;
                switch (consts.model) {
                    case "manipulator":
                        robots[msg.name] = new Manipulator(scene, consts);
                        break;
                    case "segway":
                        robots[msg.name] = new Segway(scene, consts);
                        break;
                    default:
                        robots[msg.name] = new Robot(scene, consts);
                        break;
                }
            }
            break;
        case "lost_client":
            robots[msg.name].remove();
            delete robots[msg.name];
            break;
        case "vector":
            robots[msg.owner].move(msg.vector);
            break;
        default:
            break;
    }
}

function initAll() {
    eventButtonConnection();
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
    //console.log("Server: "+JSON.stringify(msg));
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

function eventButtonFullscreen() {
    VRContainer.requestFullscreen();
}