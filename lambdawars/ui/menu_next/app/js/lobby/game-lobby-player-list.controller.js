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

        $scope.hasLocalSlot = function() {
            return $scope.localslotid !== undefined && $scope.localslotid !== null;
        };

        $scope.toggleReady = function() {
            if( !$scope.hasLocalSlot() ) {
                return;
            }
            $scope.updatePlayerData('ready', $scope.isPlayerReady() ? '0' : '1', $scope.localslotid);
        };

        $scope.numSlots = function() {
            return $scope.slots ? $scope.slots.length : 0;
        };

        $scope.numFilledSlots = function(slots) {
            return (slots || []).filter(function(slot) { return slot.type === 'player'; }).length;
        };

        $scope.connectionClass = function(slot) {
            var member = slot.player ? $scope.lobbymembers[slot.player.steamid] : undefined;
            if( !member || member.connectstate === undefined ) {
                return '';
            }
            return member.connectstate ? 'lb-conn-good' : 'lb-conn-bad';
        };

        // Same rule as IsEverybodyReady in the Python lobby: CPUs are always ready
        $scope.isEverybodyReady = function() {
            return ($scope.slots || []).every(function(slot) {
                return slot.type !== 'player' || slot.iscpu || $scope.isPlayerReadyByID(slot.slotid);
            });
        };

        // Explains why the game can't be launched yet, as translation key. Other problems, like not
        // enough players for the game mode, are reported in the lobby chat when launching.
        $scope.launchHint = function() {
            if( $scope.state !== 'lobbying' || !$scope.lobbytype || $scope.lobbytype.value === 'offline' ) {
                return '';
            }
            var localReady = !$scope.hasLocalSlot() || $scope.isPlayerReady();
            if( !$scope.islobbyowner ) {
                return localReady ? 'GL_HintWaitingForHost' : 'GL_HintReadyUpForHost';
            }
            if( !localReady ) {
                return 'GL_HintReadyUp';
            }
            return $scope.isEverybodyReady() ? '' : 'GL_HintWaitingForPlayers';
        };

        $scope.canLaunch = function() {
            return $scope.state === 'lobbying' && !$scope.launchHint();
        };

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
                    curSlots.push(slot);
                    if( i === slots.length -1 || (i < slots.length -1 && slot.team !== slots[i+1].team) ) {
                        teamSlots.push({
                            'header' : slot.team === 0 ? translations.GL_FreeForAll : translations.GL_Team + ' ' + (slot.team - 1),
                            'team' : slot.team,
                            'slots' : curSlots,
                        });
                        curSlots = [];
                    }
                }

                // The slots are tracked by id in the view, so only changed slots are redrawn
                $scope.slots = slots;
                $scope.teamSlots = teamSlots;
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