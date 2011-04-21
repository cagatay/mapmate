/*global google, goog */

var mapOptions = {
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    streetViewControl: false,
    scrollwheel: false,
    scaleControl: false,
    navigationControl: false,
    mapTypeControl: false,
    keyboardShortcuts: false
};

/* augment google latlng */
google.maps.LatLng.prototype.getLoc = function () {
    var loc = {};
    loc.lat = this.lat();
    loc.lng = this.lng();
    return loc;
};

var mapmate = {};

FB.init({
    appId: '194734940551571',
    status: true,
    cookie: true,
    xfbml: true
});

function createMap() {
    var map = new google.maps.Map($("#map-canvas")[0], mapOptions);
    map.fitBounds(mapmate.bounds);
    mapmate.map = map;
}

/* socket callbacks */
function onMessage(message) {
    message = JSON.parse(message.data);
    console.log(message);
}

function onOpen() {
    createMap();
}

function openChannel() {
    var channel = new goog.appengine.Channel(mapmate.me.token);
    mapmate.socket = channel.open({onopen: onOpen, onmessage: onMessage});
}

function getUser() {
    $.post('/user', JSON.stringify({location: mapmate.geolocation.getLoc()}), function (data) {
        mapmate.me = data;
        var sw = new google.maps.LatLng(data.box.sw.lat,
                                    data.box.sw.lon);
        var ne = new google.maps.LatLng(data.box.ne.lat,
                                    data.box.ne.lon);
        mapmate.bounds = new google.maps.LatLngBounds(sw, ne);
        openChannel();
    }, 'json');
}


/* geolocation callbacks */
function getLocation(position) {
    mapmate.geolocation = new google.maps.LatLng(position.coords.latitude,
                                                 position.coords.longitude);
    getUser();
}

function locationError(error) {
    console.log(error);
}


/* facebook callbacks */
function checkSession(response) {
    if(response.session) {
        window.main();
    }
    else {
        console.log('event: fb logout');
    }
}

/* global event handlers */
FB.Event.subscribe('auth.sessionChange', checkSession);

function main() {
    navigator.geolocation.getCurrentPosition(getLocation, locationError);
}

$(function () {
    FB.getLoginStatus(checkSession);
});
