/*global google, goog */

FB.init({
    appId: '159835304059396',
    status: true,
    cookie: true,
    xfbml: true
});

/* utility functions */
function _i(str) {
    return document.getElementById(str);
}

function _c(str) {
    return document.getElementsByClassName(str);
}

function _h(str) {
    if (str instanceof String) {
        window.location.hash = str;
    } else {
        return window.location.hash;
    }
}

function _r(str) {
    window.location.pathname = str;
}

function _e(e, c) {
    window.addEventListener(e, c, false);
}

function _a(args) {
	var method, data, async, callback, x;
    method = typeof args.method === 'undefined' ? 'POST' : args.method;
    data = typeof args.data === 'undefined' ? null : args.data;
    async = typeof args.async === 'undefined' ? true : args.async;
    callback = typeof args.callback === 'undefined' ? null : args.callback;

    x = new XMLHttpRequest();
    x.open(method, args.path, async);
    if (async) {
        x.onreadystatechange = function (e) {
            if (x.readyState === 4 && x.status === 200 && args.callback) {
                callback(x.responseText);
            }
        };
    }

    x.send(data);
    if (!async) {
        if (x.status === 200) {
            return x.responseText;
        }
    }
}
/* end utility functions */

/* augment google latlng */
google.maps.LatLng.prototype.getLoc = function () {
    var loc = {};
    loc.lat = this.lat();
    loc.lng = this.lng();
    return loc;
};
/* end augment google latlng */

/* globals */
var socket = null;
var debugLoc = new google.maps.LatLng(40.98878, 28.872195);
var app;

var mapOptions = {
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    streetViewControl: false,
    scrollwheel: false,
    scaleControl: false,
    navigationControl: false,
    mapTypeControl: false,
    keyboardShortcuts: false,
    disableDoubleClickZoom: true,
    draggable: false,
    disableDefaultUI: false
};

function onMessage(message) {
    function callHandler(obj, arg) {
        var handler = obj.type;
        if (!(typeof handler === 'undefined' ||
                     handler === 'ok' ||
                     handler === 'error')) {
            app.handlers[handler](arg);
        }
    }

    var res, len, type, i;
    if (message) {
        if (message.data) {
            res = JSON.parse(message.data);
            if (res instanceof Array) {
                len = res.lenght;
                for (i = 0; i < len; i += 1) {
                    callHandler(res[i]);
                }
            } else {
                callHandler(res);
            }
        }
    }
}

function onClose() {
    app.close();
}

function post(data, async) {
    var args = {}, res;
    args.data = JSON.stringify(data);
    args.path = '/channel';
    args.async = async;
    args.callback = onMessage;
    
    res = _a(args);
    if (res) {
        res = JSON.parse(res);
        return res.data;
    }
}

function handleState() {
    var parts, id, param, view;

    parts = _h().split('?');
    id = parts[0];
    param = parts[1];
    view = _c('active_view')[0];
    if (app.views[id]) {
        app.views[id](param);
        _i(id).className += ' active_view';
    }
    if (view) {
        view.className = 'view';
    }
}

function getLocation() {
    navigator.geolocation.getCurrentPosition(function (position) {
        app.loc = new google.maps.LatLng(position.coords.latitude,
                                         position.coords.longitude);
        app.init();
        // google.maps.event.addListener(state.map, 'tilesloaded', function () { var bounds = state.map.getBounds();
        //});		        
    }, function (error) {
    	/* for debug only
    	 * write this function properly before production
    	 */
        app.loc = debugLoc;
        app.init();
    });
}	

function onOpen() {
    getLocation();
}

function main() {
    app.main();
}

function openChannel(token) {
	var channel, handler;
	channel = new goog.appengine.Channel(token);
	handler = {
		'onopen'    : onOpen,
		'onmessage' : onMessage,
        'onclose'   : onClose
	};
	socket = channel.open(handler);
}

function close() {
    socket.close();
}
/* end globals */

/* mate object */
function Mate(data) {
    this.key = data.key;
    this.name = data.name;
    this.pic = '/pic?id=' + this.key;
    this.loc = new google.maps.LatLng(data.location.lat, data.location.lng);
}

Mate.prototype.addMarker = function (map) {
    var key = this.key;
    this.marker = new google.maps.Marker({
        position : this.loc.googleLoc,
        map      : map,
        title    : this.name,
        icon     : this.pic
    });
    google.maps.event.addListener(this.marker, 'click', function () {
        _h('#profile?' + key);
    });
};

/* end mate object */

/* application object */
app = {
    token : null,
    map : null,
    loc : null,
    bounds : null,
    receivedMessages : [],
    sentMessages : [],
    mates : {},

    views : {
        profile : function (id) {
            var pr = app.mates[id];
            _i("profile_header").innerHTML = pr.name;
            _i("profile_pic").setAttribute("src", pr.pic);
            _i("profile_id").innerHTML = pr.key;
        }
    },

    main : function () {
        this.requestToken();
        openChannel(this.token);
    },

    init : function () {
        var data = {
            "func" : "rpc_init",
            "location" : this.loc.getLoc()
        };
        post(data);
    },

    close : function () {
        var data = {
            "func"	: "rpc_close"
        };
        post(data);
    },

    requestToken : function () {
        var data, res;
        data = {
            'func' : 'rpc_get_token'
        };
        res = post(data, false);
        if (res.type === 'authError') {
            this.handlers.authError();
        } else {
	    this.token = res.token;
        }
    },

    createMap : function () {
        mapOptions.center = this.loc;
        this.map = new google.maps.Map(_i("map-canvas"), mapOptions);
        this.map.fitBounds(this.bounds);
    },

    postMessage : function () {
        var text, recipient, param;
        text = _i("message_body").value;
        recipient = _i("profile_id").value;
       
        param = {
            "func" : "rpc_send_message",
            "text" : text,
            "recipient" : recipient
        };
        post(param);
        _h("");
    },


    handlers : {
        updateMap : function (data) {
            var bounds, ne, sw;
            bounds = data.bounds;
            ne = new google.maps.LatLng(bounds.ne.lat, bounds.ne.lng);
            sw = new google.maps.LatLng(bounds.sw.lat, bounds.sw.lng);
            app.bounds = new google.maps.LatLngBounds(sw, ne);
            if (app.map) {
                app.updateMap();
            } else {
                app.createMap();
            }
        },

        addMate : function (data) {
            var userid = data.key;
            if (typeof app.mates[userid] === 'undefined') {
                app.mates[userid] = new Mate(data);
                app.mates[userid].addMarker(app.map);
            }
        },

        removeMate : function (data) {
            app.mates[data.key].marker.setMap(null);
            delete app.mates[data.key];
        },

        authError : function () {
            window.location.pathname = '/oauth';
        },

        updateState : function () {
        // TODO: implement
            return;
        },

        receivedMessage : function (data) {
        // TODO: implement
            alert(data.text);
        },

        sentMessage : function (data) {
        // TODO: implement
        }
    }
};
/* end app object */

_e('load', main);
_e('hashchange', handleState);
_e('unload', close);
