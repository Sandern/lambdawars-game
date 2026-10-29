'use strict';

import menuModule from './module';

const STATE_UPDATE_INTERVAL = 1000;

class WorkshopBrowseController {
    /*@ngInject*/
    constructor($scope, $timeout, $interval) {
        $scope.pageID = 'page';

        $scope.loading = false;
        $scope.error = '';
        $scope.items = [];
        $scope.total = 0;
        $scope.numpages = 0;
        $scope.selected = null;
        $scope.filter = {
            page: 1,
            sort: 'trend',
            list: 'all',
            search: '',
            searchinput: '',
        };
        // Shown as tabs
        $scope.lists = [
            {value: 'all', label: 'WB_Tab_Browse'},
            {value: 'subscribed', label: 'WB_Tab_Subscribed'},
            {value: 'mine', label: 'WB_Tab_Mine'},
        ];
        // Relevance needs search text, which Steam only supports when listing all maps.
        // Sorting by title is only supported for lists of the player.
        var sorts = [
            {value: 'relevance', label: 'WB_Sort_Relevance', all: true, user: false},
            {value: 'trend', label: 'WB_Sort_Trend', all: true, user: false},
            {value: 'toprated', label: 'WB_Sort_TopRated', all: true, user: true},
            {value: 'subscriptions', label: 'WB_Sort_Subscriptions', all: true, user: false},
            {value: 'newest', label: 'WB_Sort_Newest', all: true, user: true},
            {value: 'updated', label: 'WB_Sort_Updated', all: true, user: true},
            {value: 'title', label: 'WB_Sort_Title', all: false, user: true},
        ];

        if( !('workshopbrowser' in window) ) {
            $scope.error = 'Workshop browser component not loaded';
            return;
        }

        $scope.sortOptions = function() {
            var isAll = $scope.filter.list === 'all';
            return sorts.filter(function(sort) {
                if( sort.value === 'relevance' ) {
                    return isAll && $scope.filter.search;
                }
                return isAll ? sort.all : sort.user;
            });
        };

        // Keeps the selected sort valid for the current list and search
        function fixSort() {
            var options = $scope.sortOptions();
            var valid = options.some(function(sort) { return sort.value === $scope.filter.sort; });
            if( !valid ) {
                $scope.filter.sort = options.length ? options[0].value : 'newest';
            }
        }

        var queryId = 0;
        $scope.load = function(page) {
            $scope.filter.page = page || 1;
            $scope.loading = true;
            $scope.error = '';
            $scope.selected = null;

            var id = ++queryId;
            workshopbrowser.query($scope.filter.page, $scope.filter.sort, $scope.filter.search, $scope.filter.list,
                function(success, error, items, total, numpages) {
                    // Called from Python, outside of the angular digest cycle
                    $timeout(function() {
                        if( id !== queryId ) {
                            return;
                        }
                        $scope.loading = false;
                        $scope.error = success ? '' : error;
                        $scope.items = items;
                        $scope.total = total;
                        $scope.numpages = numpages;
                    });
                });
        };

        $scope.search = function() {
            var search = ($scope.filter.searchinput || '').trim();
            if( search && !$scope.filter.search ) {
                $scope.filter.sort = 'relevance';
            }
            $scope.filter.search = search;
            fixSort();
            $scope.load(1);
        };

        $scope.clearSearch = function() {
            $scope.filter.searchinput = '';
            $scope.search();
        };

        $scope.changeList = function() {
            fixSort();
            $scope.load(1);
        };

        $scope.selectList = function(list) {
            if( list === $scope.filter.list ) {
                return;
            }
            $scope.filter.list = list;
            $scope.changeList();
        };

        $scope.emptyTitle = function() {
            if( $scope.filter.search && $scope.filter.list === 'all' ) {
                return 'WB_EmptySearch';
            }
            return {all: 'WB_NoResults', subscribed: 'WB_EmptySubscribed', mine: 'WB_EmptyMine'}[$scope.filter.list];
        };

        $scope.changeSort = function() {
            $scope.load(1);
        };

        $scope.goToPage = function(page) {
            if( page < 1 || page > $scope.numpages || page === $scope.filter.page || $scope.loading ) {
                return;
            }
            $scope.load(page);
        };

        // Subscribing
        $scope.isSubscribed = function(item) {
            return item.state === 'subscribed' || item.state === 'downloading' || item.state === 'installed' || item.state === 'rejected';
        };

        $scope.toggleSubscription = function(item, $event) {
            if( $event ) {
                $event.stopPropagation();
            }
            if( $scope.isSubscribed(item) ) {
                workshopbrowser.unsubscribe(item.id);
                item.state = 'none';
            } else {
                workshopbrowser.subscribe(item.id);
                item.state = 'subscribed';
            }
        };

        $scope.stateLabel = function(item) {
            switch( item.state ) {
                case 'downloading': return 'WB_State_Downloading';
                case 'installed': return 'WB_State_Installed';
                case 'subscribed': return 'WB_State_Subscribed';
                case 'rejected': return 'WB_State_Rejected';
                default: return '';
            }
        };

        $scope.stateIcon = function(item) {
            return {downloading: 'download', installed: 'check', subscribed: 'clock', rejected: 'block'}[item.state] || '';
        };

        // Longer text of the state, in the details
        $scope.stateText = function(item) {
            return {
                downloading: 'WB_StateText_Downloading',
                installed: 'WB_StateText_Installed',
                subscribed: 'WB_StateText_Subscribed',
                rejected: 'WB_StateText_Rejected',
            }[item.state] || '';
        };

        // Details
        $scope.showDetails = function(item) {
            $scope.selected = item;
        };

        $scope.closeDetails = function() {
            $scope.selected = null;
        };

        $scope.openItemPage = function(item) {
            if( 'workshop' in window ) {
                workshop.openitem(item.id);
            }
        };

        // Formatting
        $scope.rating = function(item) {
            var votes = item.votesup + item.votesdown;
            return votes > 0 ? Math.round(100 * item.votesup / votes) : null;
        };

        $scope.ratingClass = function(item) {
            var rating = $scope.rating(item);
            return rating >= 70 ? 'ws-ok' : (rating >= 40 ? '' : 'ws-error');
        };

        $scope.formatSize = function(bytes) {
            if( !bytes ) {
                return '-';
            }
            if( bytes < 1024 * 1024 ) {
                return Math.max(1, Math.round(bytes / 1024)) + ' KB';
            }
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        };

        $scope.formatDate = function(timestamp) {
            return timestamp ? new Date(timestamp * 1000).toLocaleDateString([], {day: 'numeric', month: 'short', year: 'numeric'}) : '-';
        };

        // A map that is still being published from the publish page, shown above the maps
        // {mapname, title, publishedfileid, progress}, and its result once finished {success, message}
        $scope.upload = null;
        $scope.uploadResult = null;
        if( 'workshop' in window ) {
            // Called from Python, outside of the angular digest cycle
            workshop.sethandler({
                OnPublishProgress: function(status, processed, total) {
                    $timeout(function() {
                        if( $scope.upload ) {
                            $scope.upload.progress = total > 0 ? Math.round(100 * processed / total) : 0;
                        }
                    });
                },
                OnReviewProgress: function() {},
                OnPublishFinished: function(success, publishedfileid, message) {
                    $timeout(function() {
                        if( $scope.upload ) {
                            $scope.uploadResult = {success: success, message: message, publishedfileid: publishedfileid};
                        }
                    });
                },
            });
            workshop.getpublishstate(function(upload) {
                $timeout(function() {
                    if( upload ) {
                        upload.progress = upload.total > 0 ? Math.round(100 * upload.processed / upload.total) : 0;
                    }
                    $scope.upload = upload;
                });
            });
        }

        $scope.dismissUpload = function() {
            $scope.upload = null;
            $scope.uploadResult = null;
        };

        // Keeps subscription states and author names up to date
        var stateUpdate = $interval(function() {
            if( !$scope.items.length ) {
                return;
            }
            var itemIds = $scope.items.map(function(item) { return item.id; });
            var ownerIds = $scope.items.filter(function(item) { return !item.author; }).map(function(item) { return item.owner; });
            workshopbrowser.getstates(itemIds, ownerIds, function(states, names) {
                $timeout(function() {
                    $scope.items.forEach(function(item) {
                        var state = states[item.id];
                        if( state ) {
                            item.state = state.state;
                            item.progress = state.progress;
                            item.error = state.error;
                        }
                        if( !item.author && names[item.owner] ) {
                            item.author = names[item.owner];
                        }
                    });
                });
            });
        }, STATE_UPDATE_INTERVAL);

        $scope.$on('$destroy', function() {
            $interval.cancel(stateUpdate);
        });

        $scope.load(1);
    }

}

menuModule.controller('WorkshopBrowseController', WorkshopBrowseController);
