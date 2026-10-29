'use strict';

import menuModule from './module';

const VISIBILITY_PRIVATE = 2;

// Publishing a new map or updating one of the player's Workshop maps. The list on the left holds "publish a
// new map" and the player's Workshop items; updates are reviewed in a dialog before uploading.
class WorkshopController {
    /*@ngInject*/
    constructor($scope, $rootScope, $timeout, $routeParams, $filter) {
        $scope.pageID = 'page';
        var translate = $filter('translate');

        // 'new' to publish a new map, 'item' to update the selected Workshop item (entry)
        $scope.mode = 'new';
        $scope.entry = null;
        $scope.newMaps = [];
        // The review, upload and result are shown in a dialog
        $scope.dialogOpen = false;
        $scope.confirmNew = false;

        $scope.loaded = false;
        $scope.available = false;
        $scope.error = '';
        $scope.maps = [];
        $scope.selected = {map: null};
        $scope.form = {};
        $scope.publishing = false;
        // The map being uploaded {mapname, title, publishedfileid}, kept after the upload for the result
        $scope.upload = null;
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
                        isnew: $scope.mode === 'new',
                    };
                    if( publishedfileid && $scope.selected.map ) {
                        $scope.selected.map.publishedfileid = publishedfileid;
                    }
                    if( success && $scope.selected.map ) {
                        $scope.selected.map.lastupload = Math.floor(Date.now() / 1000);
                    }
                    // A newly published map is added to the list of Workshop items, and selected
                    updateWorkshopItems();
                    if( publishedfileid && $scope.mode === 'new' ) {
                        selectEntryById(publishedfileid, true);
                    }
                    $scope.dialogOpen = true;
                });
            },
        });

        // The minimap of the selected map {state, res, image, src, positions}, loaded by Python (see GetMapMinimap)
        $scope.minimap = null;
        $scope.minimapLoading = false;
        var minimapMapName = null;
        var lastMinimapId = 0;
        function loadMinimap(map) {
            var name = map ? map.name : null;
            if( name === minimapMapName ) {
                return;
            }
            minimapMapName = name;
            var minimapId = ++lastMinimapId;
            $scope.minimap = null;
            $scope.minimapLoading = !!map;
            if( !map ) {
                return;
            }
            workshop.getminimap(name, function(minimap) {
                $timeout(function() {
                    if( minimapId !== lastMinimapId ) {
                        return;
                    }
                    $scope.minimapLoading = false;
                    $scope.minimap = minimap;
                });
            });
        }

        // Generating the minimap: the map is loaded to capture it from above, then the game returns to this page
        // (see menu/workshop/minimapgen.py). minimapDialog is confirm, review (approve or discard) or failed.
        $scope.minimapDialog = null;
        $scope.generated = null;
        $scope.minimapError = '';
        $scope.savingMinimap = false;

        $scope.canGenerateMinimap = function() {
            return $scope.available && $scope.selected.map && !$scope.publishing && !$scope.linking;
        };

        $scope.confirmGenerateMinimap = function() {
            if( $scope.canGenerateMinimap() ) {
                $scope.minimapError = '';
                $scope.minimapDialog = 'confirm';
            }
        };

        $scope.generateMinimap = function() {
            var map = $scope.selected.map;
            if( !$scope.canGenerateMinimap() ) {
                return;
            }
            // The unsaved details come back with the page after leaving the map (see workshop:minimapgenerated)
            $rootScope.workshopDraft = {mapname: map.name, form: angular.copy($scope.form)};
            workshop.generateminimap(map.name, function(error) {
                $timeout(function() {
                    if( error ) {
                        $rootScope.workshopDraft = null;
                        $scope.minimapError = error;
                    }
                });
            });
        };

        $scope.closeMinimapDialog = function() {
            $scope.minimapDialog = null;
        };

        $scope.discardMinimap = function() {
            workshop.discardminimap();
            $scope.generated = null;
            $scope.minimapDialog = null;
        };

        $scope.approveMinimap = function() {
            if( !$scope.generated || $scope.savingMinimap ) {
                return;
            }
            $scope.savingMinimap = true;
            workshop.approveminimap($scope.generated.mapname, function(error, minimap) {
                $timeout(function() {
                    $scope.savingMinimap = false;
                    if( error ) {
                        $scope.minimapError = error;
                        return;
                    }
                    $scope.generated = null;
                    $scope.minimapDialog = null;
                    if( $scope.selected.map && $scope.selected.map.name === minimapMapName ) {
                        $scope.minimap = minimap;
                    }
                });
            });
        };

        // Coming back from generating: show the result for approval
        function showGeneratedMinimap() {
            workshop.getgeneratedminimap(function(generated) {
                $timeout(function() {
                    if( !generated ) {
                        return;
                    }
                    $scope.generated = generated;
                    $scope.minimapError = generated.success ? '' : generated.error;
                    $scope.minimapDialog = generated.success ? 'review' : 'failed';
                });
            });
        }

        // nomap, loading, ok, none (the map has no minimap) or missing (the minimap image isn't found)
        $scope.minimapState = function() {
            if( !$scope.selected.map ) {
                return 'nomap';
            }
            if( $scope.minimapLoading ) {
                return 'loading';
            }
            return $scope.minimap ? $scope.minimap.state : 'none';
        };

        $scope.selectMap = function() {
            var map = $scope.selected.map;
            loadMinimap(map);
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
            $scope.previewError = '';
        };

        // CEF can't provide the path of a chosen file, so a native file dialog is opened from Python
        $scope.choosingPreview = false;
        $scope.previewError = '';

        $scope.choosePreview = function() {
            if( $scope.choosingPreview || $scope.publishing ) {
                return;
            }
            var map = $scope.selected.map;
            $scope.choosingPreview = true;
            workshop.choosepreview($scope.form.preview || '', function(path, error) {
                $timeout(function() {
                    $scope.choosingPreview = false;
                    if( $scope.selected.map !== map ) {
                        return;
                    }
                    $scope.previewError = error;
                    if( path && !error ) {
                        $scope.form.preview = path;
                    }
                });
            });
        };

        $scope.clearPreview = function() {
            $scope.form.preview = '';
            $scope.previewError = '';
        };

        // Shows the chosen preview image, loaded by Python as the menu can't load local files.
        // Waits a moment after typing, so not every keystroke loads the image.
        $scope.previewImage = '';
        var previewImageTimer = null;
        var lastPreviewImageId = 0;
        $scope.$watch('form.preview', function(path) {
            $timeout.cancel(previewImageTimer);
            var previewImageId = ++lastPreviewImageId;
            $scope.previewImage = '';
            if( !path ) {
                return;
            }
            previewImageTimer = $timeout(function() {
                workshop.getpreviewimage(path, function(image, error) {
                    $timeout(function() {
                        if( previewImageId !== lastPreviewImageId ) {
                            return;
                        }
                        $scope.previewImage = image;
                        $scope.previewError = error;
                    });
                });
            }, 300);
        });

        $scope.refresh = function(done) {
            workshop.getinfo(function(available, error, maps, upload) {
                $timeout(function() {
                    var selectedName = $scope.selected.map ? $scope.selected.map.name : null;
                    $scope.loaded = true;
                    $scope.available = available;
                    $scope.error = error;
                    $scope.maps = maps;
                    $scope.publishing = !!upload;
                    // Opened during an upload: show its map and progress
                    if( upload ) {
                        $scope.upload = upload;
                        $scope.status = upload.status;
                        $scope.progress = upload.total > 0 ? Math.round(100 * upload.processed / upload.total) : 0;
                        if( upload.publishedfileid ) {
                            pendingItem = upload.publishedfileid;
                        } else {
                            $scope.mode = 'new';
                            selectedName = upload.mapname;
                        }
                    }
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
            $scope.newMaps = $scope.maps.filter(function(map) { return !map.publishedfileid; });
            // Keep the selected item, the list is rebuilt
            if( $scope.entry ) {
                $scope.entry = items.find(function(entry) { return entry.id === $scope.entry.id; }) || $scope.entry;
            }
        }

        function selectEntryById(id, keepResult) {
            var entry = $scope.workshopItems.find(function(item) { return String(item.id) === String(id); });
            if( entry ) {
                $scope.selectEntry(entry, keepResult);
            }
            return !!entry;
        }

        var pendingItem = $routeParams.item;
        function selectPendingItem() {
            if( pendingItem && selectEntryById(pendingItem) ) {
                pendingItem = null;
                restoreDraft();
            }
        }

        // ?map=<name> selects a local map, as a new map or as its Workshop item
        var pendingMap = $routeParams.map;
        function selectPendingMap() {
            var map = pendingMap ? $scope.maps.find(function(m) { return m.name === pendingMap; }) : null;
            pendingMap = null;
            if( !map ) {
                return;
            }
            if( map.publishedfileid ) {
                pendingItem = map.publishedfileid;
                selectPendingItem();
                return;
            }
            $scope.selectNew();
            $scope.selected.map = map;
            $scope.selectMap();
            restoreDraft();
        }

        // The details entered before generating a minimap
        function restoreDraft() {
            var draft = $rootScope.workshopDraft;
            if( draft && $scope.selected.map && draft.mapname === $scope.selected.map.name ) {
                $scope.form = draft.form;
                $rootScope.workshopDraft = null;
            }
        }

        // Selecting in the list
        $scope.selectNew = function() {
            if( $scope.publishing ) {
                return;
            }
            $scope.mode = 'new';
            $scope.entry = null;
            $scope.linkError = '';
            $scope.selected.map = null;
            $scope.selectMap();
        };

        // Not blocked while uploading: the list is disabled then, but the page selects the uploading item
        $scope.selectEntry = function(entry, keepResult) {
            var result = $scope.result;
            $scope.mode = 'item';
            $scope.entry = entry;
            $scope.linkError = '';
            $scope.selected.map = entry.map || null;
            $scope.selectMap();
            if( keepResult ) {
                $scope.result = result;
            }
        };

        $scope.isSelected = function(entry) {
            return $scope.mode === 'item' && $scope.entry && $scope.entry.id === entry.id;
        };

        // The item in the list that is being uploaded, null for a new map that has no id yet
        $scope.isUploading = function(entry) {
            return $scope.publishing && $scope.upload && $scope.upload.publishedfileid === (entry ? entry.id : '');
        };

        // Shows the upload again after closing the dialog
        $scope.showUpload = function() {
            $scope.dialogOpen = true;
        };

        // Items published from another PC are linked first: the item is downloaded to find its map on this PC
        $scope.linkEntry = function() {
            var entry = $scope.entry;
            if( !entry || entry.map || $scope.linking ) {
                return;
            }
            $scope.linking = true;
            $scope.linkError = '';
            $scope.reviewProgress = 0;
            workshop.linkitem(entry.id, function(success, error) {
                $timeout(function() {
                    $scope.linking = false;
                    if( !success ) {
                        $scope.linkError = error;
                        return;
                    }
                    $scope.refresh(function() {
                        selectEntryById(entry.id);
                    });
                });
            });
        };

        $scope.loadMyItems = function() {
            $scope.myItemsLoading = true;
            $scope.myItemsError = '';
            workshop.getmyitems(function(success, error, items) {
                $timeout(function() {
                    $scope.myItemsLoading = false;
                    $scope.myItemsError = success ? '' : error;
                    $scope.myItems = items;
                    updateWorkshopItems();
                    selectPendingItem();
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
            $scope.upload = {mapname: map.name, title: map.title, publishedfileid: map.publishedfileid || ''};
            $scope.status = null;
            $scope.progress = 0;
            $scope.result = null;
            workshop.publish(map.name, map.title, map.description, map.visibility,
                             $scope.update.changenote || '', map.preview);
        };

        $scope.statusLabel = function() {
            return $scope.status === null ? 'WS_Publishing' : 'WS_Status_' + $scope.status;
        };

        // The dialog: a new map is confirmed, an update is reviewed first. Then the upload and its result.
        $scope.openDialog = function() {
            if( !$scope.canPublish() ) {
                return;
            }
            $scope.result = null;
            $scope.dialogOpen = true;
            if( $scope.mode === 'new' ) {
                $scope.confirmNew = true;
            } else {
                $scope.startReview();
            }
        };

        // The upload continues in the background when the dialog is closed
        $scope.closeDialog = function() {
            $scope.dialogOpen = false;
            $scope.confirmNew = false;
            $scope.cancelReview();
            if( !$scope.publishing ) {
                $scope.result = null;
            }
        };

        $scope.dialogPhase = function() {
            if( $scope.publishing ) {
                return 'uploading';
            }
            if( $scope.result ) {
                return $scope.result.success ? 'done' : 'failed';
            }
            if( $scope.reviewing ) {
                return 'reviewing';
            }
            if( $scope.reviewError ) {
                return 'reviewerror';
            }
            if( $scope.review ) {
                return 'review';
            }
            return $scope.confirmNew ? 'confirmnew' : null;
        };

        $scope.confirmPublish = function() {
            $scope.confirmNew = false;
            $scope.publish();
        };

        $scope.retry = function() {
            $scope.publish();
        };

        $scope.fileName = function(path) {
            return (path || '').split(/[\\/]/).pop();
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

        // The line next to the review button: what is missing, or what happens next
        $scope.summary = function() {
            if( !$scope.available ) {
                return {text: 'WS_SummaryUnavailable', kind: 'error'};
            }
            if( $scope.publishing ) {
                return {text: 'WS_SummaryUploading', kind: 'info'};
            }
            if( $scope.mode === 'item' && !$scope.selected.map ) {
                return $scope.linkError ? {text: 'WS_SummaryLinkFailed', kind: 'error'} : {text: 'WS_SummaryNotLinked', kind: 'warn'};
            }
            if( !$scope.selected.map ) {
                return {text: $scope.newMaps.length ? 'WS_SummaryChooseMap' : 'WS_SummaryNoMaps', kind: 'info'};
            }
            if( !$scope.form.title ) {
                return {text: 'WS_SummaryNoTitle', kind: 'warn'};
            }
            if( $scope.mode === 'new' ) {
                return {text: 'WS_SummaryReadyNew', kind: 'ok', values: {
                    title: $scope.form.title,
                    visibility: translate($scope.visibilityLabel($scope.form.visibility)).toLowerCase(),
                }};
            }
            return {text: 'WS_SummaryReadyUpdate', kind: 'info'};
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
            return timestamp ? new Date(timestamp * 1000).toLocaleString([], {day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'}) : '';
        };

        $scope.formatDay = function(timestamp) {
            return timestamp ? new Date(timestamp * 1000).toLocaleDateString([], {day: 'numeric', month: 'short', year: 'numeric'}) : '';
        };

        $scope.openLegalAgreement = function() {
            workshop.openlegalagreement();
        };

        $scope.openItem = function(publishedfileid) {
            workshop.openitem(publishedfileid);
        };

        // The browser opens an item of the player with ?item=<id>, which may only be known after loading the items.
        // With ?progress=1 the upload is shown, when opened from the upload status of the browser.
        $scope.refresh(function() {
            selectPendingMap();
            selectPendingItem();
            if( $scope.publishing && $routeParams.progress ) {
                $scope.dialogOpen = true;
            }
            if( $routeParams.minimap ) {
                showGeneratedMinimap();
            }
            if( $scope.available ) {
                $scope.loadMyItems();
            }
        });
    }

}

menuModule.controller('WorkshopController', WorkshopController);
