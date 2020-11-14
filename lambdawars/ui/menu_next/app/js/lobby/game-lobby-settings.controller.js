'use strict';

import lobbyModule from './module';
import angular from 'angular';

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
                $scope.minimapsrc = settings.availablemaps[settings.map].overviewsrc;
                //console.log('map positions: ', settings.availablemaps[settings.map]['positioninfo']);
            } else {
                $scope.availableteamsetups = [];
                $scope.teamsetup = undefined;
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