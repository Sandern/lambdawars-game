'use strict';

import lobbyModule from './module';
import angular from 'angular';

/**
 * Game Lobby factory.
 * @ngInject
 */
function GamelobbyServiceFactory($rootScope, $location, $routeParams, ChatlobbyService, $translate, recent) {
    var GamelobbyService = function(/*broadcastname*/) {
        ChatlobbyService.apply(this, arguments);
        
        this.welcomeMsg = "";
        this.state = 'none';
        this.isoffline = false;
        this.clearData();
        this.notifyUserEnterLeft = true;
        this.showDialogOnLobbyCreateFail = true;
        
        var self = this;
        $rootScope.$on('lobbying:msg', function(event, msg) {
            $translate(msg).then(function (translatedMsg) {
                self.lobbyingstate_msg = translatedMsg;
            });
        });
    };
    
    GamelobbyService.prototype = new ChatlobbyService();
    
    GamelobbyService.prototype.clearData = function() {
        this.settings = {};
        this.slots = [];
        this.lobbyingstate_msg = null;
        this.pendingPreset = null;
    };
    
    GamelobbyService.prototype.setState = function(state) {
        if( this.state === state ) { 
            return; 
        }
        var oldstate = this.state;
        this.state = state;
        
        if( oldstate === 'gamestarted' && state === 'lobbying' ) {
            this.lobbyingstate_msg = 'GL_StatusGameEndedContinue';
        }
        
        $rootScope.$broadcast("gamelobby:statechange", state, oldstate);
        
        if( state === 'none' ) {
            this.clearData();
            if( this.isoffline ) {
                $location.path('/Singleplayer');
            } else {
                $location.path('/Multiplayer');
            }
        } else if( state === 'joining' ) {
            $location.path('/Gamelobby');
        }
    };
    GamelobbyService.prototype.setStateWithApply = function(state) {
        var _self = this;
        $rootScope.$apply(function() {
            _self.setState(state);
        });
    };
    
    // A preset ("Host again" on the home page) holds the settings of an earlier game, applied
    // once the lobby is created
    GamelobbyService.prototype.createLobby = function(preset) {
        this.setState('creating');
        this.isoffline = $routeParams.lobbytype === 'offline';
        this.pendingPreset = preset ? angular.copy(preset) : null;
        gamelobby.createlobby('New lobby', $routeParams.lobbytype);
    };

    // Applies one setting per lobby update, since the available maps depend on the mode and the
    // team setups on the map. Settings that are no longer available are skipped.
    GamelobbyService.prototype.applyPreset = function(settings) {
        var preset = this.pendingPreset;
        if( !preset || !settings.islobbyowner ) {
            return;
        }
        if( preset.mode && settings.mode !== preset.mode && !preset.triedMode ) {
            preset.triedMode = true;
            if( settings.availablemodes && settings.availablemodes[preset.mode] ) {
                this.setSetting('mode', preset.mode);
                return;
            }
        }
        if( preset.map && settings.map !== preset.map && !preset.triedMap ) {
            preset.triedMap = true;
            if( settings.availablemaps && settings.availablemaps[preset.map] ) {
                this.setSetting('map', preset.map);
                return;
            }
        }
        if( preset.teamsetup && settings.teamsetup !== preset.teamsetup && !preset.triedTeamsetup ) {
            preset.triedTeamsetup = true;
            var map = settings.availablemaps ? settings.availablemaps[settings.map] : null;
            if( map && map.supportedmodes.indexOf(preset.teamsetup) !== -1 ) {
                this.setSetting('teamsetup', preset.teamsetup);
                return;
            }
        }
        this.pendingPreset = null;
        var customfields = settings.customfields || {};
        for( var key in preset.customfields || {} ) {
            var field = customfields[key];
            var value = preset.customfields[key];
            if( field && field.selectedvalue !== value && field.values.indexOf(value) !== -1 ) {
                this.setCustomField(key, value);
            }
        }
    };

    // Remembers the settings of a launched game for "Host again" on the home page
    GamelobbyService.prototype.rememberGame = function() {
        var settings = this.settings;
        if( !settings || !settings.islobbyowner ) {
            return;
        }
        var map = settings.availablemaps ? settings.availablemaps[settings.map] : null;
        var mode = settings.availablemodes ? settings.availablemodes[settings.mode] : null;
        var customfields = {};
        var nummodifiers = 0;
        for( var key in settings.customfields || {} ) {
            var field = settings.customfields[key];
            customfields[key] = field.selectedvalue;
            if( field.values[0] === 'no' && field.selectedvalue !== 'no' ) {
                nummodifiers++;
            }
        }
        recent.setLastGame({
            lobbytype: settings.lobbytype,
            mode: settings.mode,
            modename: mode ? mode.name : settings.mode,
            map: settings.map,
            overviewsrc: map ? map.overviewsrc : '',
            teamsetup: settings.teamsetup,
            customfields: customfields,
            nummodifiers: nummodifiers,
        });
    };
    
    GamelobbyService.prototype.joinLobby = function(lobbysteamid) {
        this.setState('joining');
        this.isoffline = false;
        gamelobby.joinlobby(lobbysteamid);
    };
    
    GamelobbyService.prototype.leaveLobby = function() {
        console.log('Leaving game lobby');
        gamelobby.leavelobby();
        this.setState('none'); // Note: will also be changed by the game progress, but with a delay.
        this.isoffline = false;
    };
    
    GamelobbyService.prototype.launch = function() {
        this.rememberGame();
        gamelobby.launch();
    };
    
    GamelobbyService.prototype.cancel_launch = function() {
        gamelobby.cancel_launch();
    };
    
    GamelobbyService.prototype.setSetting = function(key, value) {
        //console.log('Setting "' + key + '" to value: ' + value);
        gamelobby.setSetting(key, value);
    };
    
    GamelobbyService.prototype.setPlayerData = function(key, value, slotid) {
        //console.log('Setting player data "' + key + '" to value: ' + value);
        gamelobby.setPlayerData(key, value, slotid);
    };
    
    GamelobbyService.prototype.setCustomField = function(key, value) {
        //console.log('Setting custom field data "' + key + '" to value: ' + value);
        gamelobby.setCustomField(key, value);
    };
    
    GamelobbyService.prototype.setMMPassword = function(mm_password) {
        gamelobby.setMMPassword(mm_password);
    };
    
    // Callbacks from handler
    GamelobbyService.prototype.OnCreateLobbyFailed = function(/*errorcode, msg*/) {
        ChatlobbyService.prototype.OnCreateLobbyFailed.apply(this, arguments);
        
        this.setState('none');
        this.isoffline = false;
    };
    
    GamelobbyService.prototype.OnJoinOrCreateLobby = function(/*users*/) {
        ChatlobbyService.prototype.OnJoinOrCreateLobby.apply(this, arguments);
        var _self = this;
        $translate('GL_WelcomeGameLobby').then(function (welcomeMsg) {
            _self.OnLobbyChatMsg("", welcomeMsg);
        });
    };
    
    GamelobbyService.prototype.OnLobbyDataChanged = function(settings, lobbymembers, slots) {
        this.settings = settings;
        this.slots = slots;
        this.applyPreset(settings);
        
        $rootScope.$apply(function() {
            $rootScope.$broadcast("gamelobby:settings", settings);

            $rootScope.$broadcast("gamelobby:lobbymembers", lobbymembers);

            $rootScope.$broadcast("gamelobby:slots", slots);
        });
    };
    
    return GamelobbyService;
}

lobbyModule.factory('GamelobbyService', GamelobbyServiceFactory);

/**
 * @ngInject
 */
function gamelobbymanager(GamelobbyService) {
    return new GamelobbyService('gamelobby');
}

lobbyModule.factory('gamelobbymanager', gamelobbymanager);