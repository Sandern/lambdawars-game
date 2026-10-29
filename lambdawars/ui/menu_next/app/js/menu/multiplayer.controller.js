'use strict';

import menuModule from './module';

var DISCORD_URL = 'https://discord.gg/SdAtwCJhrH';
var LOBBY_LIST_INTERVAL = 10000;

class MultiplayerController {
    /*@ngInject*/
    constructor($scope, gamelobbylist, gamelobbymanager, chatdrawer) {
		$scope.pageID = 'page';

        $scope.loaded = false;
        $scope.lobbies = [];
        $scope.waiting = [];

        function onLobbiesUpdated() {
            $scope.$applyAsync(function() {
                $scope.loaded = true;
                $scope.lobbies = gamelobbylist.lobbies.map(gamelobbylist.describe);
                $scope.waiting = gamelobbylist.waitingForPlayers($scope.lobbies);
            });
        }
        gamelobbylist.startUpdating(onLobbiesUpdated, LOBBY_LIST_INTERVAL);
        $scope.$on('$destroy', function() {
            gamelobbylist.stopUpdating(onLobbiesUpdated);
        });

        $scope.joinlobby = function(steamid) {
            gamelobbymanager.joinLobby(steamid);
        };

        $scope.openDiscord = function() {
            gameui.openurl(DISCORD_URL);
        };

        $scope.openChat = function() {
            chatdrawer.open = true;
        };

        $scope.openserverbrowser = function() {
            gameui.clientcommand('openserverbrowser');
        };
    }

}

menuModule.controller('MultiplayerController', MultiplayerController);
