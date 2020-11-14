'use strict';

import menuModule from './module';

const unknownMissionImg = require("../../images/unknown.png");
const nullMissionImg = require("../../images/null.png");

class MissionsController {
    /*@ngInject*/
    constructor($scope, missions) {
        $scope.pageID = 'content';
        
        $scope.mapname = missions.mapname;
        $scope.description = missions.description;
        $scope.selectedDifficulty = "normal";
        
        $scope.leftmissionpic = unknownMissionImg;
        $scope.middlemissionpic = unknownMissionImg;
        $scope.rightmissionpic = unknownMissionImg;
        
        $scope.updateInfo = function() {
            var preventry = missions.missions[missions.missions_index-1];
            var nextentry = missions.missions[missions.missions_index+1];
            var entry = missions.missions[missions.missions_index];
            if( entry !== undefined ) {
                $scope.mapname = entry.mapname;
                $scope.description = entry.description;
                $scope.middlemissionpic = entry.image || unknownMissionImg;
            } else {
                $scope.mapname = 'Unknown';
                $scope.description = '';
                $scope.middlemissionpic = unknownMissionImg;
            }
            
            if( preventry !== undefined ) {
                $scope.leftmissionpic = preventry.image || unknownMissionImg;
            } else {
                $scope.leftmissionpic = nullMissionImg;
            }
            if( nextentry !== undefined ) {
                $scope.rightmissionpic = nextentry.image || unknownMissionImg;
            } else {
                $scope.rightmissionpic = nullMissionImg;
            }
        };
        
        $scope.next_mission = function() {
            if( missions.missions_index < missions.missions.length-1 ) {
                missions.missions_index++;
                $scope.updateInfo();
            }
        };
        $scope.previous_mission = function() {
            if( missions.missions_index > 0 ) {
                missions.missions_index--;
                $scope.updateInfo();
            }
        };
        
        $scope.launch_mission = function() {
            var entry = missions.missions[missions.missions_index];
            if( entry !== undefined ) {
                gameui.launchmission(entry.mapname, $scope.selectedDifficulty);
            } else {
                console.error('Invalid mission selected!');
            }
        };
        
        missions.update(function() {
            $scope.updateInfo();
            $scope.$digest();
        });
    }

}

menuModule.controller('MissionsController', MissionsController);