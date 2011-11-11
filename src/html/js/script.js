/*global google, goog */

FB.init({
    appId: '194734940551571',
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
        case 'new-chat':
            app.newChat(message.chat);
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
    
    try {
        switch (id) {
            case 'profile':
                app.showProfile(param);
                _i(id).className += ' active_view';
                break;
            case 'messages':
                app.createChatView();
                _i(id).className += ' active_view';
                break;
            case 'chat':
                app.showChat(param);
                _i(id).className += ' active_view';
                break;
            case 'main':
                _i(id).className += ' active_view';
                break;
        }
    }
    catch (err){
        console.error(err);
        _h('');
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
            _h('#main');
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
    chats : {
        list : {}
    },
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
            app.getChats();
            app.getMates();

        });
    },

    close : function () {
        _a('DELETE', '/user', null);
        return;
    },

    createMap : function () {
        mapOptions.center = this.loc;
        this.map = new google.maps.Map(_i("map-canvas"), mapOptions);
        this.map.fitBounds(this.bounds);
        google.maps.event.addListener(this.map, 'bounds_changed', function () {
            this.fitBounds(app.bounds);
        });
    },

    getChats : function () {
        var chatlist = _i('chat-list');
        var chattemplate = _i('chat-list-template');
        _a('GET', '/chat', null, function (chats) {
            for(var i in chats) {
                if(chats.hasOwnProperty(i)) {
                    var chat = chats[i];
                    app.chats.list[chat.other.fb_uid] = chat;
                }
            }
            app.updateUnreadCount();
            console.log(app.chats);
        });
        return;
    },

    createChatView : function () {
        var chatlist = _i('chat-list');
        var template = _i('chat-template');
        var elem, children, img, span, link, count = '';

        while(chatlist.hasChildNodes()){
            chatlist.removeChild(chatlist.firstChild);
        }

        for(var i in app.chats.list) {
            if(app.chats.list.hasOwnProperty(i)) {
                chat = app.chats.list[i];
                elem = template.cloneNode(true);
                elem.removeAttribute('id');
                elem.setAttribute('href', '#chat?' + chat.other.fb_uid);
                img = elem.getElementsByTagName('img')[0];
                img.setAttribute('src', 'http://graph.facebook.com/' + chat.other.fb_uid + '/picture');
                span = elem.getElementsByTagName('span')[0];
                span.innerHTML = chat.last_message_text;
                elem.className = '';
                chatlist.insertBefore(elem, chatlist.firstChild);
            }
        }
        return;
    },

    updateUnreadCount : function () {
        var unread = 0, chats = this.chats.list, count = '';
        for(var c in chats) {
            if(chats.hasOwnProperty(c)) {
                if(!chats[c].read) {
                    unread ++;
                }
            }
        }
        link = _i('messages-link');
        if(unread) {
            count = ' (' + unread + ')';
        }
        link.innerHTML = 'messages' + count;
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
        if (fb_uid !== this.me.fb_uid && !this.mates[fb_uid]) {
            this.mates[fb_uid] = new Mate(mate);
        }
    },

    removeMate : function (uid) {
        app.mates[uid].marker.setMap(null);
        delete app.mates[uid];
    },

    newChat : function (chat) {
        this.chats.list[chat.other.fb_uid] = chat;
        this.updateUnreadCount();
        return;
    },

    postMessage : function (uid) {
        var textArea = _i('message-text');
        var message = {
            text : textArea.value,
            reciepent : uid
        };

        _a('POST', '/message', message, function (response) {
            console.log(response);
            textArea.value = '';
        }, false);

    },

    showProfile : function (id) {
        var dd, dt, pr = app.mates[id];
        _i('profile-pic').setAttribute('src', pr.pic);
        _i('send-message').setAttribute('href', '#chat?' + id);

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
    },

    showChat : function (uid) {
        var but = _i('post-message');
        var messagelist = _i('message-list');
        _a('GET', '/message?uid=' + uid, null, function (messages) {
            if(!app.chats.list[uid]) {
                app.chats.list[uid] = {};
            }
            app.chats.list[uid].messages = messages;
            console.log(messages);
        }, false);

        while(messagelist.hasChildNodes()) {
            messagelist.removeChild(messagelist.firstChild);
        }

        var message, messages = this.chats.list[uid].messages;
        for(var m in messages) {
            if(messages.hasOwnProperty(m)) {
                message = messages[m];
                var template = _i('message-template');
                var elem = template.cloneNode(true);
                elem.removeAttribute('id');
                var img = elem.getElementsByTagName('img')[0];
                img.setAttribute('src', 'http://graph.facebook.com/' + message.sender.fb_uid + '/picture');
                var span = elem.getElementsByTagName('span')[0];
                span.innerHTML = message.text;
                messagelist.appendChild(elem);
            }
        }
        but.dataset.uid = uid;
        this.chats.list[uid].read = true;
        this.updateUnreadCount();
    }
        
};
/* end app object */

_e('load', main);
_e('hashchange', handleState);
_e('unload', close);
_i('post-message').addEventListener('click', function () {
    app.postMessage(this.dataset.uid);
}, false);
FB.Event.subscribe('auth.sessionChange', function (response) {
    if(response.session) {
        _h('#main');
        getLocation();
    }
});
