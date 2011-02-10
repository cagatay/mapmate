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
    if (typeof str === 'undefined') {
        return window.location.hash;
    } else {
        window.location.hash = str;
    }
}

function _r(str) {
    window.location.pathname = str;
}

function _e(e, c) {
    window.addEventListener(e, c, false);
}

function _a(method, path, data, callback, async) {
    if (data !== null) {
        data = JSON.stringify(data);
    }

    function p(response) {
        res = JSON.parse(response).data;
        if (res.type === 'error') {
            alert(res.error);
        } else {
            if (callback) {
                callback(res);
            }
        }
    }

    var res;
    async = true ? async : false;

    x = new XMLHttpRequest();
    x.open(method, path, async);
    if (async) {
        x.onreadystatechange = function (e) {
            if (x.readyState === 4 && x.status === 200 && args.callback) {
                p(x.responseText);
            }
        };
    }

    x.send(data);
    if (!async) {
        if (x.status === 200) {
            p(x.responseText);
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
    keyboardShortcuts: false
};

function onMessage(message) {
    message = JSON.parse(message.data);
    console.log(message);
    switch(message.type) {
        case 'add-mate':
            app.addMate(message.mate);
            break;
        case 'remove-mate':
            app.removeMate(message.uid);
            break;
    }
}

function onOpen() {
    return;
}

function handleState() {
    var parts, id, param, view;

    parts = _h().split('?');
    id = parts[0].substring(1);
    param = parts[1];
    view = _c('active_view')[0];
    
    switch (id) {
        case 'profile':
            app.showProfile(param);
            _i(id).className += ' active_view';
            break;
        case 'messages':
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
        app.start();
    }, function (error) {
        /* for debug only
          write this function properly before production */
        app.loc = debugLoc;
        app.start();
    });
}	

function main() {
    FB.getLoginStatus(function (response) {
        if(response.session) {
            handleState();
            getLocation();
        }
    });
}

function openChannel(token) {
	var channel, handler;
	channel = new goog.appengine.Channel(token);
	handler = {
        'onopen' : onOpen,
		'onmessage' : onMessage
	};
	socket = channel.open(handler);
}

function close() {
    socket.close();
    app.close();
}
/* end globals */

/* mate object */
function Mate(data) {
    var fb_uid = data.fb_uid;
    this.fb_uid = fb_uid;
    this.pic = 'http://graph.facebook.com/' + fb_uid + '/picture';
    this.loc = new google.maps.LatLng(data.location.lat, data.location.lon);
    this.marker = new google.maps.Marker({
        position : this.loc,
        map      : app.map,
        icon     : this.pic
    });
    google.maps.event.addListener(this.marker, 'click', function () {
        _h('#profile?' + fb_uid);
    });
}

/* end mate object */

/* application object */
app = {
    receivedMessages : [],
    sentMessages : [],
    mates : {},

    start : function () {
        var data = {
            location : this.loc.getLoc()
        };

        _a('POST', '/user', data, function (user) {
            app.me = user;

            sw = new google.maps.LatLng(user.box.sw.lat,
                                        user.box.sw.lon);
            ne = new google.maps.LatLng(user.box.ne.lat,
                                        user.box.ne.lon);
            app.bounds = new google.maps.LatLngBounds(sw, ne);

            app.createMap();
            openChannel(app.me.token);
            app.getMessages();
            app.getMates();

        });
    },

    close : function () {
        _a('DELETE', '/user', null);
    },

    createMap : function () {
        mapOptions.center = this.loc;
        this.map = new google.maps.Map(_i("map-canvas"), mapOptions);
        this.map.fitBounds(this.bounds);
        google.maps.event.addListener(this.map, 'bounds_changed', function () {
            this.fitBounds(app.bounds);
        });
    },

    getMessages : function () {
        return;
    },

    getMates : function () {
        _a('GET', '/user', null, function (mates) {
            var len = mates.length, i;
            for(i = 0; i < len; i ++) {
                if (mates[i].fb_uid !== app.me.fb_uid) {
                    app.mates[mates[i].fb_uid] = new Mate(mates[i]);
                }
            }
            return;
        });
        return;
    },

    addMate : function (mate) {
        var fb_uid = mate.fb_uid;
        if (fb_uid !== this.me.fb_uid) {
            this.mates[fb_uid] = new Mate(mate);
        }
    },

    removeMate : function (uid) {
        app.mates[uid].marker.setMap(null);
        delete app.mates[uid];
    },

    showProfile : function (id) {
        var dd, dt, pr = app.mates[id];
        _i("profile-pic").setAttribute("src", pr.pic);

        FB.api('/' + id, function (response) {
            var profileInfo = _i('profile-info');
            _i('profile-name').innerHTML = response.first_name;

            while (profileInfo.childNodes[0]) {
                profileInfo.removeChild(profileInfo.childNodes[0]);
            }


            for (var item in response) {
                if (response.hasOwnProperty(item)) {
                    dt = document.createElement('dt');
                    dt.innerHTML = item;
                    dd = document.createElement('dd');
                    dd.innerHTML = response[item];
                    profileInfo.appendChild(dt);
                    profileInfo.appendChild(dd);
                }
            }
                    
            console.log(response);
        });
    }
};
/* end app object */

_e('load', main);
_e('hashchange', handleState);
_e('unload', close);
FB.Event.subscribe('auth.sessionChange', function (response) {
    if(response.session) {
        handleState();
        getLocation();
    }
});
