'use strict';

import lobbyModule from './module';

/* Game Lobby 
 * @ngInject
 */
 function GamelobbyServiceFactory($rootScope, $location, $routeParams, ChatlobbyService, $translate) {
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
    
    GamelobbyService.prototype.createLobby = function() {
        this.setState('creating');
        this.isoffline = $routeParams.lobbytype === 'offline';
        gamelobby.createlobby('New lobby', $routeParams.lobbytype);
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
        
        $rootScope.$apply(function() {
            $rootScope.$broadcast("gamelobby:settings", settings);

            $rootScope.$broadcast("gamelobby:lobbymembers", lobbymembers);

            $rootScope.$broadcast("gamelobby:slots", slots);
        });
    };
    
    return GamelobbyService;
}
lobbyModule.factory('GamelobbyService', GamelobbyServiceFactory);

/*@ngInject*/
function gamelobbymanager(GamelobbyService) {
    return new GamelobbyService('gamelobby');
}
lobbyModule.factory('gamelobbymanager', gamelobbymanager);