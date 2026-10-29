'use strict';

import lobbyModule from './module';
import angular from 'angular';

var STANDARD_TEAM_SETUPS = ['1vs1', '2vs2', '3vs3', '4vs4'];

class GamelobbySettingsController {
    /*@ngInject*/
    constructor($scope, gamelobbymanager) {
        $scope.availablemodes = [];
        $scope.availablemaps = [];
        $scope.availableteamsetups = [];
        $scope.customfields = {};
        
        $scope.mode = undefined;
        $scope.map = undefined;
        $scope.teamsetup = undefined;
        $scope.selectedCustomFields = {};
        $scope.minimapsrc = '';
        $scope.teamSetupOptions = [];
        $scope.modifiersOpen = false;
        // Workshop info of the selected map ({author, subscribed}), shown on the map card.
        // Visual only for now: filled by the Workshop integration.
        $scope.mapworkshop = null;

        $scope.teamSetupLabel = function(teamsetup) {
            return teamsetup === 'FFA' ? teamsetup : teamsetup.replace(/vs/g, 'v');
        };

        // The common team setups are always shown, the ones the map doesn't support are disabled
        $scope.buildTeamSetupOptions = function(supportedmodes) {
            var ids = supportedmodes.indexOf('FFA') !== -1 ? ['FFA'] : [];
            STANDARD_TEAM_SETUPS.concat(supportedmodes).forEach(function(id) {
                if( ids.indexOf(id) === -1 ) {
                    ids.push(id);
                }
            });
            return ids.map(function(id) {
                return {id: id, label: $scope.teamSetupLabel(id), supported: supportedmodes.indexOf(id) !== -1};
            });
        };

        $scope.selectTeamSetup = function(option) {
            if( !$scope.islobbyowner || !option.supported || $scope.isPlayerReady() ) {
                return;
            }
            if( !$scope.teamsetup || $scope.teamsetup.id !== option.id ) {
                $scope.updateSetting('teamsetup', option.id);
            }
        };

        $scope.numCustomFields = function() {
            return Object.keys($scope.customfields || {}).length;
        };

        $scope.customFieldsSummary = function() {
            return Object.keys($scope.customfields || {}).map(function(key) {
                return $scope.selectedCustomFields[key];
            }).filter(function(value) { return value; }).join(', ');
        };

        $scope.toggleModifiers = function() {
            $scope.modifiersOpen = !$scope.modifiersOpen;
        };

        $scope.updateGameInfoFromSettings = function(settings) {
            // Update available settings if needed
            if( !angular.equals($scope.availablemodes, settings.availablemodes ) ) {
                $scope.availablemodes = settings.availablemodes;
            }
            if( !angular.equals($scope.availablemaps, settings.availablemaps ) ) {
                $scope.availablemaps = settings.availablemaps;
            }
            if( !angular.equals($scope.customfields, settings.customfields ) ) {
                $scope.customfields = settings.customfields;
            }
            
            // Fix current selection if needed
            $scope.mode = $scope.fixSelectedDropdown(settings.mode, $scope.availablemodes);
            $scope.map = $scope.fixSelectedDropdown(settings.map, $scope.availablemaps);
            
            for( var key in $scope.customfields ) {
                $scope.selectedCustomFields[key] = $scope.fixSelectedArrayDropdown($scope.customfields[key].selectedvalue, $scope.customfields[key].values);
            }
            
            if( settings.availablemaps && settings.availablemaps.hasOwnProperty(settings.map) ) {
                var supportedmodes = [];
                for( var i = 0; i < settings.availablemaps[settings.map].supportedmodes.length; i++ ) {
                    var mode = settings.availablemaps[settings.map].supportedmodes[i];
                    supportedmodes[mode] = {
                        'id' : mode,
                        'name' : mode,
                    };
                }
                $scope.availableteamsetups = supportedmodes;
                $scope.teamsetup = $scope.fixSelectedDropdown(settings.teamsetup, $scope.availableteamsetups);
                var teamSetupOptions = $scope.buildTeamSetupOptions(settings.availablemaps[settings.map].supportedmodes);
                if( !angular.equals($scope.teamSetupOptions, teamSetupOptions) ) {
                    $scope.teamSetupOptions = teamSetupOptions;
                }
                $scope.minimapsrc = settings.availablemaps[settings.map].overviewsrc;
                //console.log('map positions: ', settings.availablemaps[settings.map]['positioninfo']);
            } else {
                $scope.availableteamsetups = [];
                $scope.teamsetup = undefined;
                $scope.teamSetupOptions = [];
                $scope.minimapsrc = '';
            }
        };
        
        $scope.$on('gamelobby:settings', function(event, settings) {
            $scope.updateGameInfoFromSettings(settings);
        });
        if( gamelobbymanager.settings !== undefined ) {
            $scope.updateGameInfoFromSettings(gamelobbymanager.settings);
        }
    }

}

lobbyModule.controller('GamelobbySettingsController', GamelobbySettingsController);