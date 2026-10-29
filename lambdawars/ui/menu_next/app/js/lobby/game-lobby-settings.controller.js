'use strict';

import lobbyModule from './module';
import angular from 'angular';
import { teamSetupLabel } from '../core/format';

var STANDARD_TEAM_SETUPS = ['1vs1', '2vs2', '3vs3', '4vs4'];

// Translation keys for the common custom field values, other values are shown capitalized
var VALUE_LABELS = {
    'no': 'GL_ModOff',
    'yes': 'GL_ModOn',
    'inverted': 'GL_ModInverted',
};

// Custom fields that can be turned off ("no") and on ("yes") are modifiers, shown in the
// modifiers panel. Other custom fields, like the Overrun difficulty, are game settings.
function isModifierField(field) {
    var values = field.values || [];
    return values[0] === 'no' && values.indexOf('yes') !== -1;
}

class GamelobbySettingsController {
    /*@ngInject*/
    constructor($scope, $window, $filter, gamelobbymanager) {
        $scope.availablemodes = [];
        $scope.availablemaps = [];
        $scope.availableteamsetups = [];
        $scope.customfields = {};
        $scope.settingFields = [];
        $scope.modifierFields = [];

        $scope.mode = undefined;
        $scope.map = undefined;
        $scope.teamsetup = undefined;
        $scope.selectedCustomFields = {};
        $scope.minimapsrc = '';
        $scope.mapname = '';
        $scope.mapstatus = undefined;
        $scope.mapworkshop = null;
        $scope.mapwaiting = [];
        $scope.minimapurl = '';
        
        // Overview of the map, or the Workshop preview image if the map has no overview (yet)
        function updateMinimapUrl() {
            if( $scope.minimapsrc ) {
                $scope.minimapurl = $scope.minimapsrc + '.vtf';
            } else {
                $scope.minimapurl = $scope.mapworkshop ? $scope.mapworkshop.previewurl : '';
            }
        }

        $scope.subscribeWorkshopMap = function() {
            gamelobby.subscribeWorkshopMap();
        };

        $scope.openWorkshopPage = function() {
            if( $scope.mapworkshop && 'workshop' in window ) {
                window.workshop.openitem($scope.mapworkshop.id);
            }
        };

        $scope.teamSetupOptions = [];
        $scope.modifiersOpen = false;
        $scope.modifiersStyle = {};

        $scope.teamSetupLabel = teamSetupLabel;

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

        // Custom fields: game settings and modifiers
        $scope.buildCustomFieldLists = function() {
            var fields = Object.keys($scope.customfields || {}).map(function(id) {
                var field = $scope.customfields[id];
                return {id: id, name: field.name || id, values: field.values || []};
            });
            $scope.settingFields = fields.filter(function(field) { return !isModifierField(field); });
            $scope.modifierFields = fields.filter(isModifierField).sort(function(a, b) {
                return a.name.localeCompare(b.name);
            });
            if( !$scope.modifierFields.length ) {
                $scope.closeModifiers();
            }
        };

        $scope.valueLabel = function(value) {
            if( value === undefined || value === null ) {
                return '';
            }
            value = String(value);
            return VALUE_LABELS[value] || value.charAt(0).toUpperCase() + value.slice(1);
        };

        $scope.canEditCustomFields = function() {
            return $scope.islobbyowner && !$scope.isPlayerReady();
        };

        $scope.isModifierActive = function(field) {
            var value = $scope.selectedCustomFields[field.id];
            return !!value && value !== field.values[0];
        };

        $scope.activeModifiers = function() {
            return $scope.modifierFields.filter($scope.isModifierActive);
        };

        // Active modifiers by name, with the value when it's not simply on ("Armor (Inverted)")
        $scope.modifiersSummary = function() {
            return $scope.activeModifiers().map(function(field) {
                var value = $scope.selectedCustomFields[field.id];
                return value === 'yes' ? field.name : field.name + ' (' + $filter('translate')($scope.valueLabel(value)) + ')';
            }).join(', ');
        };

        $scope.setModifier = function(field, value) {
            if( !$scope.canEditCustomFields() || $scope.selectedCustomFields[field.id] === value ) {
                return;
            }
            $scope.selectedCustomFields[field.id] = value;
            $scope.updateCustomField(field.id, value);
        };

        $scope.toggleModifier = function(field) {
            $scope.setModifier(field, $scope.isModifierActive(field) ? field.values[0] : 'yes');
        };

        $scope.resetModifiers = function() {
            $scope.activeModifiers().forEach(function(field) {
                $scope.setModifier(field, field.values[0]);
            });
        };

        // The panel opens to the left of the settings column, level with the modifiers row.
        // It's fixed positioned, so the scrolling settings column doesn't cut it off.
        var modifiersRow = null;

        function positionModifiers() {
            var row = modifiersRow.getBoundingClientRect();
            var side = angular.element(modifiersRow).closest('.lb-side')[0].getBoundingClientRect();
            $scope.modifiersStyle = {
                right: ($window.innerWidth - side.left + 16) + 'px',
                bottom: Math.max(16, $window.innerHeight - row.bottom) + 'px',
            };
        }

        $scope.toggleModifiers = function(event) {
            if( $scope.modifiersOpen ) {
                $scope.closeModifiers();
                return;
            }
            modifiersRow = event.currentTarget;
            positionModifiers();
            $scope.modifiersOpen = true;
        };

        $scope.closeModifiers = function() {
            $scope.modifiersOpen = false;
        };

        function onWindowResize() {
            if( $scope.modifiersOpen ) {
                $scope.$apply(positionModifiers);
            }
        }
        angular.element($window).on('resize', onWindowResize);
        $scope.$on('$destroy', function() {
            angular.element($window).off('resize', onWindowResize);
        });

        $scope.updateGameInfoFromSettings = function(settings) {
            // Shown while the map is not available yet, for example while downloading it from the Workshop
            $scope.mapname = settings.map;
            $scope.mapstatus = settings.mapstatus;
            $scope.mapworkshop = settings.mapworkshop || null;
            $scope.mapwaiting = settings.mapwaiting || [];

            // Update available settings if needed
            if( !angular.equals($scope.availablemodes, settings.availablemodes ) ) {
                $scope.availablemodes = settings.availablemodes;
            }
            if( !angular.equals($scope.availablemaps, settings.availablemaps ) ) {
                $scope.availablemaps = settings.availablemaps;
            }
            if( !angular.equals($scope.customfields, settings.customfields ) ) {
                $scope.customfields = settings.customfields;
                $scope.buildCustomFieldLists();
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
                updateMinimapUrl();
                //console.log('map positions: ', settings.availablemaps[settings.map]['positioninfo']);
            } else {
                $scope.availableteamsetups = [];
                $scope.teamsetup = undefined;
                $scope.teamSetupOptions = [];
                $scope.minimapsrc = '';
                updateMinimapUrl();
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
