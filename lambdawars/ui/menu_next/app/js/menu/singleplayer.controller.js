'use strict';

import menuModule from './module';
import { teamSetupLabel } from '../core/format';

class SingleplayerController {
    /*@ngInject*/
    constructor($scope, $location, missions, recent) {
		$scope.pageID = 'page';

        $scope.loaded = false;
        $scope.missions = [];
        $scope.missionImage = '';

        // Play again: the last played mission, on the same difficulty
        var lastMission = recent.lastMission();
        $scope.lastMission = null;
        if( lastMission ) {
            $scope.lastMissionDifficulty = missions.difficultyLabel(lastMission.difficulty);
        }

        missions.update(function() {
            $scope.$applyAsync(function() {
                $scope.loaded = true;
                $scope.missions = (missions.missions || []).map(missions.describe);
                $scope.lastMission = lastMission ? $scope.missions.filter(function(mission) {
                    return mission.mapname === lastMission.mapname;
                })[0] || null : null;
                var cardMission = $scope.lastMission || $scope.missions.filter(function(mission) { return mission.image; })[0];
                $scope.missionImage = cardMission ? cardMission.image : '';
            });
        });

        // Opens the mission select with this mission selected
        $scope.selectMission = function(mission) {
            missions.missions_index = $scope.missions.indexOf(mission);
            $location.path('/Missions');
        };

        $scope.launching = false;
        $scope.playAgain = function() {
            if( !$scope.lastMission || $scope.launching ) {
                return;
            }
            $scope.launching = true;
            recent.setLastMission(lastMission.mapname, lastMission.difficulty);
            gameui.launchmission(lastMission.mapname, lastMission.difficulty);
        };

        // Skirmish again: the last game, if it was an offline skirmish
        var lastGame = recent.lastGame();
        if( lastGame && lastGame.lobbytype === 'offline' ) {
            $scope.lastSkirmish = lastGame;
            $scope.lastSkirmishTitle = lastGame.modename + (lastGame.teamsetup && lastGame.mode !== 'overrun' ? ' · ' + teamSetupLabel(lastGame.teamsetup) : '');
        }

        $scope.playtutorial = function() {
            gameui.creategametutorial();
        };
    }

}

menuModule.controller('SingleplayerController', SingleplayerController);
