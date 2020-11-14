'use strict';

import lobbyModule from './module';

/* Base service for a simple lobby (just users and chat)
 * @ngInject
 */
function ChatlobbyServiceFactory($rootScope, $translate, $sanitize, $timeout, gameservice, ngDialog, badgesService) {
    var ChatlobbyService = function(broadcastname) {
        this.broadcastname = broadcastname;
        this.lobbybinding = undefined;
        this.lobbyusers = {};
        this.mutedusers = {}; // Map to muted users steamids
        this.idcount = 0;
        this.history = [];
        this.notifyUserEnterLeft = false;
        this.welcomeMsg = "Chat_WelcomeMsg";
        this.showDialogOnLobbyCreateFail = false;
    };

    ChatlobbyService.prototype.init = function(lobbybinding) {
        this.lobbybinding = lobbybinding;
        lobbybinding.sethandler(this);
    };

    ChatlobbyService.prototype.leavelobby = function() {
        this.lobbybinding.leavelobby();
    };

    ChatlobbyService.prototype.setlobbyname = function(lobbyname) {
        this.lobbybinding.setlobbyname(lobbyname);
    };
    ChatlobbyService.prototype.setlobbytype = function(lobbytype) {
        this.lobbybinding.setlobbytype(lobbytype);
    };

    var basePath = '../../mainmenu/';
    var mapObj = {
        '#star':'<img src="'+basePath+'smilies/star.png" />',
        '#st':'<img src="'+basePath+'smilies/star.png" />',
        '#rebel':'<img src="'+basePath+'smilies/rebel.png" />',
        '#r':'<img src="'+basePath+'smilies/rebel.png" />',
        '#combine':'<img src="'+basePath+'smilies/combine.png" />',
        '#c':'<img src="'+basePath+'smilies/combine.png" />',
        '#lambda':'<img src="'+basePath+'smilies/lambda.png" />',
        '#l':'<img src="'+basePath+'smilies/lambda.png" />',
        '#nui':'<img src="'+basePath+'smilies/nui.png" />',

        '#smile':'<img src="'+basePath+'smilies/smile.png" />',
        '#s':'<img src="'+basePath+'smilies/smile.png" />',
        '#sad':'<img src="'+basePath+'smilies/sad.png" />',
        '#ss':'<img src="'+basePath+'smilies/sad.png" />',
        '#bigsmile':'<img src="'+basePath+'smilies/bigsmile.png" />',
        '#bs':'<img src="'+basePath+'smilies/bigsmile.png" />',
        '#dead':'<img src="'+basePath+'smilies/dead.png" />',
        '#ds':'<img src="'+basePath+'smilies/dead.png" />',
        '#angry':'<img src="'+basePath+'smilies/angry.png" />',
        '#a':'<img src="'+basePath+'smilies/angry.png" />',
        '#stare':'<img src="'+basePath+'smilies/stare.png" />',
        '#sta':'<img src="'+basePath+'smilies/stare.png" />',
        '#cry':'<img src="'+basePath+'smilies/cry.png" />',

        '#no':'<img src="'+basePath+'smilies/no.png" />',
        '#yes':'<img src="'+basePath+'smilies/yes.png" />',
        '#ok':'<img src="'+basePath+'smilies/ok.png" />',
        '#go':'<img src="'+basePath+'smilies/go.png" />',
        '#gl':'<img src="'+basePath+'smilies/gl.png" />',
        '#hf':'<img src="'+basePath+'smilies/hf.png" />',
        '#gg':'<img src="'+basePath+'smilies/gg.png" />',

        '#headcrab':'<img src="'+basePath+'smilies/headcrab.png" />',
        '#hc':'<img src="'+basePath+'smilies/headcrab.png" />',
        '#cookie':'<img src="'+basePath+'smilies/cookie.png" />',
        '#coo':'<img src="'+basePath+'smilies/cookie.png" />',
        '#zzz':'<img src="'+basePath+'smilies/zzz.png" />',
        '#error':'<img src="'+basePath+'smilies/error.png" />',
        '#fire':'<img src="'+basePath+'smilies/fire.png" />',
        '#luck':'<img src="'+basePath+'smilies/luck.png" />',

        '#br':'<br/>'
    };

    ChatlobbyService.prototype.analyzeChatString = function(text) {
        text = text.replace(/(#star)\b|(#st)\b|(#rebel)\b|(#r)\b|(#combine)\b|(#c)\b|(#lambda)\b|(#l)\b|(#nui)\b|(#smile)\b|(#s)\b|(#sad)\b|(#ss)\b|(#bigsmile)\b|(#bs)\b|(#dead)\b|(#ds)\b|(#angry)\b|(#a)\b|(#stare)\b|(#sta)\b|(#cry)\b|(#no)\b|(#yes)\b|(#ok)\b|(#go)\b|(#gg)\b|(#gl)\b|(#hf)\b|(#gg)\b|(#headcrab)\b|(#hc)\b|(#cookie)\b|(#coo)\b|(#zzz)\b|(#error)\b|(#fire)\b|(#luck)\b|(#br)\b/gi, function(matched){
            return mapObj[matched];
        });

        return text;
    };

    /*var entityMap = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': '&quot;',
        "'": '&#39;',
        "/": '&#x2F;'
    };*/

    var devIds = [
        '76561197967932376', // Sandern
        '76561197970934689', // ProgSys
        '76561197974982763', // JJ
        '76561198034846730', // HevCrab
        '76561197989598431', // Pandango
        '76561197995806465', // Mr Darkness
        '76561197975989080', // SBeast
		'76561198188813547', // BarraBarraTigr
        '76561198223952276', // Mr.Lazy
        '76561198129908002', // PouchyBoi
        '76561198040689115', // Despot Romanicus
    ];

    var badgesPromise = badgesService.getBadges();

    function escapeText(text) {
        var SURROGATE_PAIR_REGEXP = /[\uD800-\uDBFF][\uDC00-\uDFFF]/g;
        var NON_ALPHANUMERIC_REGEXP = /([^#-~| |!])/g;
        return text.
            replace(/&/g, '&amp;').
            replace(SURROGATE_PAIR_REGEXP, function(value) {
                var hi = value.charCodeAt(0);
                var low = value.charCodeAt(1);
                return '&#' + (((hi - 0xD800) * 0x400) + (low - 0xDC00) + 0x10000) + ';';
            }).
            replace(NON_ALPHANUMERIC_REGEXP, function(value) {
            return '&#' + value.charCodeAt(0) + ';';
            }).
            replace(/</g, '&lt;').
            replace(/>/g, '&gt;');
    }

    ChatlobbyService.prototype.OnLobbyChatMsg = function(usersteamid, text) {
        // TODO: breaks off when encountering invalid html
        // Should just fall back to escaping or something
        // Don't use $sanitize, it's too permissive (although safe)
        //text = $sanitize(text);
        text = escapeText(text);

        var username = "";
        if( usersteamid.length !== 0 ) {
            //console.log('muted: ', this.mutedusers, usersteamid, this.mutedusers[usersteamid] === true);
            if( this.mutedusers[usersteamid] === true ) {
                return;
            }

            var userinfo = this.lobbyusers[usersteamid];
            username = escapeText(userinfo.username);
        }

        var type = 'user';
        if( username.length === 0 ) {
            type = 'global';
        } else {
            for (var i = 0; i < devIds.length; i++) {
                if (devIds[i] === usersteamid) {
                    type = 'admin';
                    break;
                }
            }
        }

        // Remove and and from text string
        text = this.analyzeChatString(text);
        //add badges

        var icon = '';
        var icontooltip = '';

        badgesPromise.then(function(data){
            for (var badgeIdx = 0; badgeIdx < data.data.badges.length; badgeIdx++){
                for (var idIdx = 0; idIdx < data.data.badges[badgeIdx].ids.length; idIdx++){
                    if (data.data.badges[badgeIdx].ids[idIdx].id === usersteamid) {
                        icon = data.data.badges[badgeIdx].image;
                        icontooltip = data.data.badges[badgeIdx].tooltip;
                        break;
                    }
                }
            }
        });

        $timeout(() =>{
            this.history.push({
                id:this.idcount,
                text: text,
                username: username+':',
                steamid: usersteamid,
                type: type,
                icon: icon,
                icontooltip: icontooltip
            });
            this.idcount++;
        });

        $rootScope.$broadcast(this.broadcastname+":receivedline", username, usersteamid, text, type);
    };
    ChatlobbyService.prototype.OnJoinOrCreateLobby = function(users) {
        this.lobbyusers = users;
        // For testing:
        /*for (var userid in lobbyusers) {
            var username = lobbyusers[userid]['username'];
            console.log('User entered: ' + username);
            OnLobbyChatMsg("", 'User entered: ' + username);
        }*/
    };

    ChatlobbyService.prototype.OnCreateLobbyFailed = function(errorcode, msg) {
        console.log('Failed to create lobby (error: ' + errorcode + ', msg: ' + msg + ')');
        var _self = this;
        $translate(msg).then(function (translatedErrorMsg) {
            if( _self.showDialogOnLobbyCreateFail ) {
                //_self.OnLobbyChatMsg("", translatedErrorMsg);

                ngDialog.open({
                    template: 'genericMsg',
                    className: 'ngdialog-theme-wars',
                    showClose: true,
                    data : {dialog_message: translatedErrorMsg}
                });
            }
        });
    };

    ChatlobbyService.prototype.OnLobbyChatUserEntered = function(userinfo) {
        this.lobbyusers[userinfo.steamid] = userinfo;
        var username = userinfo.username;

        if( !this.notifyUserEnterLeft ) {
            return;
        }

        var _self = this;
        $translate('Chat_UserEntered').then(function (userEnteredTranslated) {
            _self.OnLobbyChatMsg("", userEnteredTranslated + ': ' + username);
        });
        //console.log('User entered: ' + username);
    };

    ChatlobbyService.prototype.OnLobbyChatUserLeft = function(userinfo) {
        delete this.lobbyusers[userinfo.steamid];
        var username = userinfo.username;

        if( !this.notifyUserEnterLeft ) {
            return;
        }

        var _self = this;
        $translate('Chat_UserLeft').then(function (userLeftTranslated) {
            _self.OnLobbyChatMsg("", userLeftTranslated + ': ' + username);
        });
        //console.log('User left: ' + username);
    };

    ChatlobbyService.prototype.OnLobbyUserKicked = function(userinfo) {
        delete this.lobbyusers[userinfo.steamid];
        var username = userinfo.username;

        if( !this.notifyUserEnterLeft ) {
            return;
        }

        var _self = this;
        $translate('Chat_UserKicked').then(function (userKickedTranslated) {
            _self.OnLobbyChatMsg("", userKickedTranslated + ': ' + username);
        });
    };

    ChatlobbyService.prototype.sendChatMessage = function(text) {
        if (text.replace(/\s/g, '').length > 0  ) {
            if (text.length > 100) {
                text = text.substring(0, 100);
            }

            // #online will show you all players currently in the lobby
            if (text === "#online") {
                var playerslist = "Users Online: ";
                for (var userid in this.lobbyusers) {
                    playerslist += this.lobbyusers[userid].username + ", ";
                }
                playerslist = playerslist.substring(0, playerslist.length - 2);
                this.OnLobbyChatMsg("",playerslist);
                return;
            }

            this.lobbybinding.sendchatmessage(text);
        }
    };

    ChatlobbyService.prototype.muteUser = function(steamid) {
        //console.log('mute user ' + steamid);
        if (steamid === gameservice.usersteamid) {
            console.log("Cannot mute yourself!");
            return;
        }
        this.mutedusers[steamid] = true;
    };
    ChatlobbyService.prototype.isUserMute = function(steamid) {
        if (this.mutedusers[steamid]) {
            return this.mutedusers[steamid];
        }
        return false;
    };

    ChatlobbyService.prototype.isYourself = function(steamid) {
        return steamid === gameservice.usersteamid;
    };

    ChatlobbyService.prototype.unmuteUser = function(steamid) {
        console.log('unmute user ' + steamid);
        this.mutedusers[steamid] = false;
    };

    return ChatlobbyService;
}

lobbyModule.factory('ChatlobbyService', ChatlobbyServiceFactory);

/*@ngInject*/
function chatlobby($rootScope, ChatlobbyService, $translate) {
    var GlobalChatService = function(/*broadcastname*/) {
        ChatlobbyService.apply(this, arguments);
    };

    GlobalChatService.prototype = new ChatlobbyService();

    GlobalChatService.prototype.init = function(/*lobbybinding*/) {
        ChatlobbyService.prototype.init.apply(this, arguments);

        if( !$rootScope.ingame ) {
            this.findAndJoinLobby();
        }
    }
    ;
    GlobalChatService.prototype.ingameStateChanged = function(event, ingame/*, ishosting, isoffline*/) {
        if( ingame ) {
            this.lobbybinding.leavelobby();
        } else {
            this.findAndJoinLobby();
        }
    };

    GlobalChatService.prototype.findAndJoinLobby = function() {
        var lobbybinding = this.lobbybinding;

        var _self = this;
        lobbybinding.listlobbies(function(chatLobbies) {
            if( chatLobbies.length === 0 ) {
                lobbybinding.createlobby('Global Chat Lobby');
            } else {
                lobbybinding.joinlobby(chatLobbies[0].steamid);
            }
            $translate(_self.welcomeMsg).then(function (welcomeMsg) {
                _self.OnLobbyChatMsg("", welcomeMsg.replace('\\n', '<br />'));
            });

        });
    };

    var globalChatInstance = new GlobalChatService('globalchat');
    return globalChatInstance;
}
lobbyModule.factory('chatlobby', chatlobby);
