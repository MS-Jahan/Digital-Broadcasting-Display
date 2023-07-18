var CURRENT_URL = window.location;
var SERVER_URL = CURRENT_URL.protocol + "//" + CURRENT_URL.hostname + (CURRENT_URL.port ? ":" + CURRENT_URL.port : "");

// check if server_url as a slash at the end
if (SERVER_URL.endsWith("/")) {
    // replace the last slash
    SERVER_URL = SERVER_URL.slice(0, -1);
}