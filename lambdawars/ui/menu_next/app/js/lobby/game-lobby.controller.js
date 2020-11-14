'use strict';

import lobbyModule from './module';

class GamelobbyController {
    /*@ngInject*/
    constructor($scope, gamelobbymanager, ngDialog) {
        $scope.pageID = 'gamelobby';
        $scope.lobbyname = '';
        $scope.lobbytype = null;
        $scope.state = gamelobbymanager.state;
        $scope.lobbysteamid = undefined; // The lobby we are in or joining
        $scope.lobby = undefined; //
        $scope.spectators = '';
        $scope.islobbyowner = false;
        $scope.lobbymembers = gamelobbymanager.lobbyusers;
        $scope.lobbyingstate_msg = gamelobbymanager.lobbyingstate_msg;

        $scope.lobbytypes = [
            {'name' : 'GL_Private', 'value' : 'private'},
            {'name' : 'GL_FriendsOnly', 'value' : 'friendsonly'},
            {'name' : 'GL_Public', 'value' : 'public'}
        ];

        $scope.updateLobbyName = function(lobbyname) {
            gamelobbymanager.setlobbyname(lobbyname);
        };
        $scope.updateLobbyType = function(lobbytype) {
            gamelobbymanager.setlobbytype(lobbytype);
        };
		
		$scope.isLobbyOwnerReady = function(){
			return $scope.isPlayerReady($scope.localslotid);
		};

        $scope.leavelobby = function() {
            gamelobbymanager.leaveLobby();
        };
        $scope.launch = function() {
            gamelobbymanager.launch();
        };
        $scope.cancel_launch = function() {
            gamelobbymanager.cancel_launch();
        };
        $scope.joingame = function() {
            gamelobby.joingame();
        };
        $scope.requestSlot = function(slotid) {
            gamelobby.requestSlot(slotid);
        };
        $scope.spectate = function() {
            gamelobby.goSpectate();
        };
        $scope.invite = function() {
            gamelobby.invite();
        };
        $scope.addCPU = function(slotid) {
            gamelobby.addCPU(slotid);
        };
        $scope.removeCPU = function(slotid) {
            gamelobby.removeCPU(slotid);
        };
        $scope.kickPlayer = function(slotid) {
            // confirm leaving
            ngDialog.open({
                template: 'confirmKickMsg',
                className: 'ngdialog-theme-wars',
                showClose: true
            }).closePromise.then(function (data) {
                if (data.value) {
                    gamelobby.kickPlayer(slotid);
                }
            });

        };
        $scope.kickPlayerBySteamID = function(steamid) {
            gamelobby.kickPlayerBySteamID(steamid);
        };

        $scope.playerClass = function(slot) {
            if( slot.type === 'open' ) {
                return ' open';
            }
            return '';
        };

        $scope.updateSetting = function(setting, value) {
            gamelobbymanager.setSetting(setting, value);
        };

        $scope.updateCustomField = function(setting, value) {
            gamelobbymanager.setCustomField(setting, value);
        };

        $scope.fixSelectedDropdown = function(targetSelection, availableValues) {
            for( var id in availableValues ) {
                if( id === targetSelection ) {
                    return availableValues[id];
                }
            }
            return undefined;
        };
        $scope.fixSelectedDiffDropdown = function(targetSelection, availableValues) {
            for( var diffid in availableValues ) {
                if( availableValues[diffid].id === targetSelection ) {
                    return availableValues[diffid];
                }
            }
            return undefined;
        };

        $scope.fixSelectedArrayDropdown = function(targetSelection, availableValues) {
            for( var i = 0; i < availableValues.length; i++ ) {
                if( availableValues[i] === targetSelection ) {
                    return availableValues[i];
                }
            }
            return undefined;
        };

        $scope.updateValues = function(targetValues, newValues) {
            for( var key in targetValues ) {
                if( newValues.hasOwnProperty(key) ) {
                    for( var valueKey in newValues[key] ) {
                        targetValues[key][valueKey] = newValues[key][valueKey];
                    }
                }
            }
        };

        $scope.setMMPassword = function(mm_password) {
            gamelobbymanager.setMMPassword(mm_password);
        };

        $scope.updateFromSettings = function(settings) {
            $scope.lobbyname = settings.name;
            $scope.islobbyowner = settings.islobbyowner;
            $scope.spectators = settings.spectators;
            $scope.localslotid = settings.localslotid;
            $scope.mm_password = settings.mm_password;
            $scope.match_uuid = settings.match_uuid;

            // Update lobby type selection
            if( settings.lobbytype === 'offline' ) {
                $scope.lobbytype = {name: 'offline', value: 'offline'};
            } else {
                for( var i = 0; i < $scope.lobbytypes.length; i++ ) {
                    if( $scope.lobbytypes[i].value === settings.lobbytype ) {
                        $scope.lobbytype = $scope.lobbytypes[i];
                        break;
                    }
                }
            }
        };

        $scope.showScores = function() {
            $scope.isShowScores = true;
        };

        $scope.backToPlayerList = function() {
            $scope.isShowScores = false;
        };

        $scope.$on('gamelobby:statechange', function(event, state/*, oldstate*/) {
            console.log('state changed to ' + state);
            $scope.state = state;
            $scope.lobbyingstate_msg = gamelobbymanager.lobbyingstate_msg;
        });

        $scope.$on('gamelobby:settings', function(event, settings) {
            $scope.updateFromSettings(settings);
        });

        $scope.$on('gamelobby:lobbymembers', function(event, lobbymembers) {
            $scope.lobbymembers = lobbymembers;
        });

        $scope.$on('gamelobby:show_scores', function(/*event*/) {
            $scope.showScores();
        });

        if( gamelobbymanager.state === 'none' ) {
            gamelobbymanager.createLobby();
        }

        if( gamelobbymanager.settings !== undefined ) {
            $scope.updateFromSettings(gamelobbymanager.settings);
        }
    }

}

lobbyModule.controller('GamelobbyController', GamelobbyController);
