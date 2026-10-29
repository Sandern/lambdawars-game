'use strict';

import menuModule from './module';

var DIFFICULTIES = ['easy', 'normal', 'hard'];
// Defaults of GetMissions in mainmenu.py when the map resource doesn't have them
var DEFAULT_NAME = 'Unknown map';
var DEFAULT_DESCRIPTION = 'No description';

function difficultyLabel(difficulty) {
    return 'Mission_' + difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
}

class MissionsController {
    /*@ngInject*/
    constructor($scope, missions, recent) {
        $scope.pageID = 'page';

        $scope.loaded = false;
        $scope.missions = [];
        $scope.visible = [];
        $scope.selected = null;
        $scope.launching = false;

        // Workshop missions come with the Workshop integration, until then all missions are official
        $scope.filter = 'all';
        $scope.filters = [
            {id: 'all', label: 'BR_All'},
            {id: 'official', label: 'MS_Official'},
            {id: 'workshop', label: 'MS_Workshop'},
        ];

        var lastMission = recent.lastMission();
        $scope.difficulties = DIFFICULTIES.map(function(id) {
            return {id: id, label: difficultyLabel(id)};
        });
        $scope.difficulty = lastMission && DIFFICULTIES.indexOf(lastMission.difficulty) !== -1 ? lastMission.difficulty : 'normal';

        function describe(mission) {
            return {
                mapname: mission.mapname,
                title: mission.name && mission.name !== DEFAULT_NAME ? mission.name : mission.mapname,
                description: mission.description && mission.description !== DEFAULT_DESCRIPTION ? mission.description : '',
                image: mission.image || '',
                workshop: !!mission.workshop,
            };
        }

        function updateVisible() {
            $scope.visible = $scope.missions.filter(function(mission) {
                return $scope.filter === 'all' || (mission.workshop ? 'workshop' : 'official') === $scope.filter;
            });
        }

        $scope.setFilter = function(filter) {
            $scope.filter = filter;
            updateVisible();
        };

        $scope.select = function(mission) {
            $scope.selected = mission;
            $scope.launching = false;
            missions.missions_index = $scope.missions.indexOf(mission);
        };

        // Previous and next go through all missions, also those filtered out
        $scope.go = function(step) {
            var count = $scope.missions.length;
            if( count ) {
                $scope.select($scope.missions[($scope.missions.indexOf($scope.selected) + step + count) % count]);
            }
        };

        $scope.position = function() {
            return ($scope.missions.indexOf($scope.selected) + 1) + ' / ' + $scope.missions.length;
        };

        $scope.setDifficulty = function(difficulty) {
            $scope.difficulty = difficulty;
        };

        $scope.difficultyLabel = function() {
            return difficultyLabel($scope.difficulty);
        };

        $scope.launch = function() {
            if( !$scope.selected || $scope.launching ) {
                return;
            }
            $scope.launching = true;
            recent.setLastMission($scope.selected.mapname, $scope.difficulty);
            gameui.launchmission($scope.selected.mapname, $scope.difficulty);
        };

        // The mission selected before, else the last played one
        missions.update(function() {
            $scope.$applyAsync(function() {
                $scope.loaded = true;
                $scope.missions = (missions.missions || []).map(describe);
                updateVisible();
                var selected = $scope.missions[missions.missions_index];
                if( !selected && lastMission ) {
                    selected = $scope.missions.filter(function(mission) { return mission.mapname === lastMission.mapname; })[0];
                }
                if( selected || $scope.missions.length ) {
                    $scope.select(selected || $scope.missions[0]);
                }
            });
        });
    }

}

menuModule.controller('MissionsController', MissionsController);
