'use strict';

import lobbyModule from './module';
import angular from 'angular';


class GamelobbyPlayerListController {
    /*@ngInject*/
    constructor($scope, gamelobbymanager, $translate) {
        $scope.unknownPlayerAvatar = require('../../images/steam-avatar-unknown.jpg');
        $scope.crownImg = require('../../images/crown_orange.png');

        $scope.teamSlots = [];
        $scope.availablefactions = [];
        $scope.selectedFaction = {};
        $scope.selectedColor = {};
        $scope.selectedDifficulty = {};
        $scope.difficultyLabels = {};

        $scope.updatePlayerData = function(setting, value, slotid) {
            var slot = $scope.slots[slotid];
            //CPU is aways ready
            if( setting === 'ready' && slot.iscpu ) {
                value = '1';
            }
			
            slot.player[setting] = value;
            gamelobbymanager.setPlayerData(setting, value, slot.iscpu ? slotid : undefined);
			//$scope.$apply();
        };
        
		$scope.isPlayerReadyByID = function(slotid) {
			var slot = $scope.slots[slotid];
			if(slot === undefined)
				return false;
				
			if(slot.iscpu)
				return true;
			
			if(slot.player['ready'] == '1')
				return true;
			else if(slot.player['ready'] == '0')
				return false;
				
			return (slot.player['ready'] === undefined)? false: slot.player['ready'];
		};
		
		$scope.isPlayerReady = function(){
			return $scope.isPlayerReadyByID($scope.localslotid); 
		}
		
        $scope.updateFromSlotSettings = function(settings) {
            if( !angular.equals($scope.availablefactions, settings.availablefactions ) ) {
                $scope.availablefactions = settings.availablefactions;
            }
            if( !angular.equals($scope.availablecolors, settings.availablecolors ) ) {
                $scope.availablecolors = settings.availablecolors;
            }
            if( !angular.equals($scope.availabledifficulties, settings.availabledifficulties ) ) {
                $scope.availabledifficulties = settings.availabledifficulties;

                $scope.availabledifficulties.forEach((diff) => {
                    $scope.difficultyLabels[diff.id] = diff.displayname;
                });
            }
        };
        
        $scope.buildTeamSlots = function(slots) {
            $translate(['GL_FreeForAll', 'GL_Team']).then(function (translations) {
                var teamSlots = [];
                var curSlots = [];
                for( var i = 0; i < slots.length; i++ ) {
                    var slot = slots[i];

                    if( slot.player ) {
                        slot.editable = $scope.state === 'lobbying' && (slot.player.islocaluser || (slot.iscpu && $scope.islobbyowner));
                        
                        if( slot.player.islocaluser || slot.iscpu ){
                            $scope.selectedFaction[slot.slotid] = $scope.fixSelectedDropdown(slot.player.faction, $scope.availablefactions);
                            $scope.selectedColor[slot.slotid] = $scope.fixSelectedDropdown(slot.player.color, $scope.availablecolors);
                            if( slot.iscpu ) {
                                $scope.selectedDifficulty[slot.slotid] = $scope.fixSelectedDiffDropdown(slot.difficulty, $scope.availabledifficulties);
                            }
                        }
                    }
                    curSlots.push({
                        slotid: slot.slotid,
                        team: slot.team
                    });
                    if( i === slots.length -1 || (i < slots.length -1 && slot.team !== slots[i+1].team) ) {
                        teamSlots.push({
                            'header' : slot.team === 0 ? translations.GL_FreeForAll : translations.GL_Team + ' ' + (slot.team - 1),
                            'slots' : curSlots,
                        });
                        curSlots = [];
                    }
                }
                
                $scope.slots = slots;
                if( !angular.equals($scope.teamSlots, teamSlots) ) {
                    $scope.teamSlots = teamSlots;
                }
            });
            
        };
        
        $scope.$on('gamelobby:settings', function(event, settings) {
            $scope.updateFromSlotSettings(settings);
        });
        $scope.$on('gamelobby:slots', function(event, slots) {
            $scope.buildTeamSlots(slots);
        });
        
        if( gamelobbymanager.settings !== undefined ) {
            $scope.updateFromSlotSettings(gamelobbymanager.settings);
        }
        $scope.buildTeamSlots(gamelobbymanager.slots);
    }

}

lobbyModule.controller('GamelobbyPlayerListController', GamelobbyPlayerListController);