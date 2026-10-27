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
        // Comparison of an update with the item on the Workshop, shown before uploading
        $scope.review = null;
        $scope.reviewing = false;
        $scope.reviewError = '';
        // Not part of the form, so entering it doesn't make the review outdated
        $scope.update = {changenote: ''};
        $scope.fieldLabels = {
            title: 'WS_Title',
            description: 'WS_Description',
            visibility: 'WS_Visibility',
        };
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
            OnReviewProgress: function(downloaded, total) {
                $timeout(function() {
                    $scope.reviewProgress = total > 0 ? Math.round(100 * downloaded / total) : 0;
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
                    if( success && $scope.selected.map ) {
                        $scope.selected.map.lastupload = Math.floor(Date.now() / 1000);
                    }
                    // A newly published map is added to the list of Workshop items
                    updateWorkshopItems();
                });
            },
        });

        $scope.selectMap = function() {
            var map = $scope.selected.map;
            $scope.result = null;
            $scope.cancelReview();
            if( !map ) {
                $scope.form = {};
                return;
            }
            $scope.form = {
                title: map.title,
                description: map.description,
                visibility: map.visibility !== undefined ? map.visibility : VISIBILITY_PRIVATE,
                preview: map.preview,
            };
            $scope.update.changenote = '';
        };

        $scope.refresh = function(done) {
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
                    updateWorkshopItems();
                    if( done ) {
                        done();
                    }
                });
            });
        };

        // The player's Workshop items: the maps published from this PC, and the items on Steam
        // published from another PC, which are linked to a local map before updating
        $scope.myItems = [];
        $scope.myItemsLoading = false;
        $scope.myItemsError = '';
        $scope.workshopItems = [];
        $scope.linking = false;
        $scope.linkError = '';

        // Not computed in the template, new objects on every digest would never settle
        function updateWorkshopItems() {
            var items = $scope.maps.filter(function(map) { return map.publishedfileid; }).map(function(map) {
                return {id: map.publishedfileid, title: map.title, map: map, lastupload: map.lastupload};
            });
            $scope.myItems.forEach(function(item) {
                if( !items.some(function(entry) { return entry.id === item.id; }) ) {
                    items.push({id: item.id, title: item.title, map: null, timeupdated: item.timeupdated});
                }
            });
            $scope.workshopItems = items;
        }

        $scope.loadMyItems = function() {
            $scope.myItemsLoading = true;
            $scope.myItemsError = '';
            workshop.getmyitems(function(success, error, items) {
                $timeout(function() {
                    $scope.myItemsLoading = false;
                    $scope.myItemsError = success ? '' : error;
                    $scope.myItems = items;
                    updateWorkshopItems();
                });
            });
        };

        $scope.updateWorkshopItem = function(entry) {
            if( $scope.publishing || $scope.reviewing || $scope.linking ) {
                return;
            }
            if( entry.map ) {
                $scope.updateItem(entry.map);
                return;
            }

            // Published from another PC: find the local map of the item first
            $scope.linking = true;
            $scope.linkError = '';
            $scope.reviewProgress = 0;
            workshop.linkitem(entry.id, function(success, error, mapname) {
                $timeout(function() {
                    $scope.linking = false;
                    if( !success ) {
                        $scope.linkError = error;
                        return;
                    }
                    $scope.refresh(function() {
                        var linked = $scope.maps.find(function(map) { return map.name === mapname; });
                        if( linked ) {
                            $scope.updateItem(linked);
                        }
                    });
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
                             $scope.update.changenote || '', map.preview);
        };

        $scope.statusLabel = function() {
            return $scope.status === null ? 'WS_Publishing' : 'WS_Status_' + $scope.status;
        };

        // Updating published maps
        $scope.updateItem = function(map) {
            if( $scope.publishing ) {
                return;
            }
            $scope.selected.map = map;
            $scope.selectMap();
            $scope.startReview();
        };

        $scope.startReview = function() {
            if( !$scope.canPublish() || !$scope.selected.map.publishedfileid ) {
                return;
            }
            var map = $scope.selected.map;
            var reviewedForm = JSON.stringify($scope.form);
            var reviewId = ++lastReviewId;
            $scope.review = null;
            $scope.reviewError = '';
            $scope.reviewing = true;
            $scope.reviewProgress = 0;
            workshop.reviewupdate(map.name, $scope.form.title, $scope.form.description || '', $scope.form.visibility,
                                  $scope.form.preview || '', function(success, error, review) {
                $timeout(function() {
                    // Only the latest review is shown, if it wasn't cancelled
                    if( reviewId !== lastReviewId || !$scope.reviewing ) {
                        return;
                    }
                    // The form was changed while reviewing, so the review is outdated
                    if( $scope.selected.map !== map || JSON.stringify($scope.form) !== reviewedForm ) {
                        $scope.reviewing = false;
                        return;
                    }
                    $scope.reviewing = false;
                    $scope.review = success ? review : null;
                    $scope.reviewError = success ? '' : error;
                });
            });
        };

        var lastReviewId = 0;

        $scope.cancelReview = function() {
            $scope.review = null;
            $scope.reviewing = false;
            $scope.reviewError = '';
        };

        $scope.confirmUpdate = function() {
            $scope.cancelReview();
            $scope.publish();
        };

        // The review shows the form values, so it's outdated when the form changes
        $scope.$watch('form', function(newValue, oldValue) {
            if( newValue !== oldValue && ($scope.review || $scope.reviewError) ) {
                $scope.cancelReview();
            }
        }, true);

        $scope.visibilityLabel = function(value) {
            var visibility = $scope.visibilities.find(function(v) { return v.value === value; });
            return visibility ? visibility.label : '';
        };

        $scope.formatSize = function(bytes) {
            if( bytes < 1024 ) {
                return bytes + ' B';
            }
            if( bytes < 1024 * 1024 ) {
                return Math.round(bytes / 1024) + ' KB';
            }
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        };

        $scope.formatDate = function(timestamp) {
            return timestamp ? new Date(timestamp * 1000).toLocaleString() : '';
        };

        $scope.openLegalAgreement = function() {
            workshop.openlegalagreement();
        };

        $scope.openItem = function(publishedfileid) {
            workshop.openitem(publishedfileid);
        };

        $scope.refresh(function() {
            if( $scope.available ) {
                $scope.loadMyItems();
            }
        });
    }

}

menuModule.controller('WorkshopController', WorkshopController);
