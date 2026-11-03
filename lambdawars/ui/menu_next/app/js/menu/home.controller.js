'use strict';

import menuModule from './module';
import { teamSetupLabel } from '../core/format';

var LOBBY_LIST_INTERVAL = 10000;
var LOBBY_TYPE_LABELS = {
    'public': 'GL_Public',
    'friendsonly': 'GL_FriendsOnly',
    'private': 'GL_Private',
    'offline': 'GL_OfflineGame',
};

class HomeController {
	/*@ngInject*/
    constructor($scope, gamelobbylist, gamelobbymanager, missions, recent) {
		$scope.pageID = 'page';

        // Lobbies
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

        // Missions: the image of the last played mission, or the first one
        $scope.lastMission = recent.lastMission();
        $scope.missionImage = '';
        if( $scope.lastMission ) {
            $scope.lastMissionDifficulty = missions.difficultyLabel($scope.lastMission.difficulty);
        }

        missions.update(function() {
            $scope.$applyAsync(function() {
                var list = missions.missions || [];
                var last = $scope.lastMission;
                var mission = list.filter(function(m) { return last && m.mapname === last.mapname; })[0] || list[0];
                $scope.missionImage = mission && mission.image ? mission.image : '';
            });
        });

        // Host again with the settings of the last hosted game
        var lastGame = recent.lastGame();
        $scope.lastGame = lastGame;
        if( lastGame ) {
            $scope.lastGameTitle = lastGame.modename + (lastGame.teamsetup && lastGame.mode !== 'overrun' ? ' · ' + teamSetupLabel(lastGame.teamsetup) : '');
            $scope.lastGameType = LOBBY_TYPE_LABELS[lastGame.lobbytype] || 'GL_Public';
            $scope.hostAgainUrl = '#!/Gamelobby?preset=last' + (lastGame.lobbytype ? '&lobbytype=' + encodeURIComponent(lastGame.lobbytype) : '');
        }

        // Your Workshop maps ({title, updated, subscribers, linked}).
        // Visual only for now: filled by the Workshop integration.
        $scope.workshopMaps = [];
    }

}

menuModule.controller('HomeController', HomeController);
