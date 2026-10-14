'use strict';

import menuModule from './module';

const VISIBILITY_PRIVATE = 2;

class WorkshopController {
    /*@ngInject*/
    constructor($scope, $timeout) {
        $scope.pageID = 'content';

        $scope.loaded = false;
        $scope.available = false;
        $scope.error = '';
        $scope.maps = [];
        $scope.selected = {map: null};
        $scope.form = {};
        $scope.publishing = false;
        $scope.status = null;
        $scope.progress = 0;
        $scope.result = null;
        $scope.visibilities = [
            {value: 0, label: 'WS_Visibility_Public'},
            {value: 1, label: 'WS_Visibility_FriendsOnly'},
            {value: 3, label: 'WS_Visibility_Unlisted'},
            {value: 2, label: 'WS_Visibility_Private'},
        ];

        if( !('workshop' in window) ) {
            $scope.loaded = true;
            $scope.error = 'Workshop component not loaded';
            return;
        }

        // Called from Python, outside of the angular digest cycle
        workshop.sethandler({
            OnPublishProgress: function(status, processed, total) {
                $timeout(function() {
                    $scope.status = status;
                    $scope.progress = total > 0 ? Math.round(100 * processed / total) : 0;
                });
            },
            OnPublishFinished: function(success, publishedfileid, message, needslegalagreement) {
                $timeout(function() {
                    $scope.publishing = false;
                    $scope.status = null;
                    $scope.result = {
                        success: success,
                        publishedfileid: publishedfileid,
                        message: message,
                        needslegalagreement: needslegalagreement,
                    };
                    if( publishedfileid && $scope.selected.map ) {
                        $scope.selected.map.publishedfileid = publishedfileid;
                    }
                });
            },
        });

        $scope.selectMap = function() {
            var map = $scope.selected.map;
            $scope.result = null;
            if( !map ) {
                $scope.form = {};
                return;
            }
            $scope.form = {
                title: map.title,
                description: map.description,
                visibility: map.visibility !== undefined ? map.visibility : VISIBILITY_PRIVATE,
                preview: map.preview,
                changenote: '',
            };
        };

        $scope.refresh = function() {
            workshop.getinfo(function(available, error, maps, publishing) {
                $timeout(function() {
                    var selectedName = $scope.selected.map ? $scope.selected.map.name : null;
                    $scope.loaded = true;
                    $scope.available = available;
                    $scope.error = error;
                    $scope.maps = maps;
                    $scope.publishing = publishing;
                    $scope.selected.map = maps.find(function(map) { return map.name === selectedName; }) || null;
                    $scope.selectMap();
                });
            });
        };

        $scope.canPublish = function() {
            return $scope.available && !$scope.publishing && $scope.selected.map && $scope.form.title;
        };

        $scope.publish = function() {
            if( !$scope.canPublish() ) {
                return;
            }
            var map = $scope.selected.map;
            // Remember the entered values in case the map is selected again
            map.title = $scope.form.title;
            map.description = $scope.form.description || '';
            map.visibility = $scope.form.visibility;
            map.preview = $scope.form.preview || '';

            $scope.publishing = true;
            $scope.status = null;
            $scope.progress = 0;
            $scope.result = null;
            workshop.publish(map.name, map.title, map.description, map.visibility,
                             $scope.form.changenote || '', map.preview);
        };

        $scope.statusLabel = function() {
            return $scope.status === null ? 'WS_Publishing' : 'WS_Status_' + $scope.status;
        };

        $scope.openLegalAgreement = function() {
            workshop.openlegalagreement();
        };

        $scope.openItem = function(publishedfileid) {
            workshop.openitem(publishedfileid);
        };

        $scope.refresh();
    }

}

menuModule.controller('WorkshopController', WorkshopController);
