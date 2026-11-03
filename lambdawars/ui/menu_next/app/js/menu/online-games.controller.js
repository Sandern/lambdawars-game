'use strict';

import menuModule from './module';

var LOBBY_LIST_INTERVAL = 15000;

// Lobbies with room first, the fullest of those first: they start soonest
var SORTS = {
    best: function(a, b) {
        return (a.isFull - b.isFull) || (b.fill - a.fill) || (b.taken - a.taken);
    },
    players: function(a, b) {
        return b.taken - a.taken;
    },
    name: function(a, b) {
        return a.name.localeCompare(b.name) || a.map.localeCompare(b.map);
    },
};

class OnlineGamesController {
    /*@ngInject*/
    constructor($scope, $interval, gamelobbylist, gamelobbymanager) {
		$scope.pageID = 'page';

        $scope.loaded = false;
        $scope.lobbies = [];
        $scope.visibleLobbies = [];
        $scope.modes = [];
        $scope.selected = null;
        $scope.filter = {
            search: '',
            mode: '',
            hideFull: false,
            sort: 'best',
        };
        $scope.sorts = [
            {id: 'best', label: 'BR_SortRecommended'},
            {id: 'players', label: 'BR_SortPlayers'},
            {id: 'name', label: 'BR_SortName'},
        ];

        // Filtering and sorting
        $scope.updateVisibleLobbies = function() {
            var search = $scope.filter.search.trim().toLowerCase();
            $scope.visibleLobbies = $scope.lobbies.filter(function(lobby) {
                if( $scope.filter.mode && lobby.mode !== $scope.filter.mode ) {
                    return false;
                }
                if( $scope.filter.hideFull && lobby.isFull ) {
                    return false;
                }
                return !search || lobby.name.toLowerCase().indexOf(search) !== -1 || lobby.map.toLowerCase().indexOf(search) !== -1;
            }).sort(SORTS[$scope.filter.sort]);

            // Keep the selected lobby, also when the list is updated
            var selectedId = $scope.selected ? $scope.selected.steamid : null;
            $scope.selected = $scope.visibleLobbies.filter(function(lobby) { return lobby.steamid === selectedId; })[0] ||
                $scope.visibleLobbies[0] || null;
        };
        $scope.$watch('filter', $scope.updateVisibleLobbies, true);

        $scope.setMode = function(mode) {
            $scope.filter.mode = mode;
        };

        $scope.toggleHideFull = function() {
            $scope.filter.hideFull = !$scope.filter.hideFull;
        };

        $scope.setSort = function(sort) {
            $scope.filter.sort = sort;
        };

        $scope.clearFilters = function() {
            $scope.filter.search = '';
            $scope.filter.mode = '';
            $scope.filter.hideFull = false;
        };

        // Selection, also with the arrow keys
        $scope.select = function(lobby) {
            $scope.selected = lobby;
        };

        $scope.onListKey = function(event) {
            var list = $scope.visibleLobbies;
            if( !list.length || (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') ) {
                return;
            }
            event.preventDefault();
            var index = list.indexOf($scope.selected) + (event.key === 'ArrowDown' ? 1 : -1);
            $scope.selected = list[Math.max(0, Math.min(list.length - 1, index))];
        };

        // Updating the list
        $scope.secondsSinceUpdate = 0;
        $scope.refreshing = false;

        function onLobbiesUpdated() {
            $scope.$applyAsync(function() {
                $scope.loaded = true;
                $scope.refreshing = false;
                $scope.secondsSinceUpdate = 0;
                $scope.lobbies = gamelobbylist.lobbies.map(gamelobbylist.describe);
                // One dot per slot, filled when taken
                $scope.lobbies.forEach(function(lobby) {
                    lobby.teams.forEach(function(team) {
                        team.dots = [];
                        for( var i = 0; i < team.total; i++ ) {
                            team.dots.push(i < team.taken);
                        }
                    });
                });

                var modes = {};
                $scope.lobbies.forEach(function(lobby) {
                    modes[lobby.mode] = lobby.modename;
                });
                $scope.modes = Object.keys(modes).sort().map(function(mode) {
                    return {id: mode, name: modes[mode]};
                });
                $scope.updateVisibleLobbies();
            });
        }
        gamelobbylist.startUpdating(onLobbiesUpdated, LOBBY_LIST_INTERVAL);

        var ticker = $interval(function() {
            $scope.secondsSinceUpdate++;
        }, 1000);

        $scope.$on('$destroy', function() {
            gamelobbylist.stopUpdating(onLobbiesUpdated);
            $interval.cancel(ticker);
        });

        $scope.refresh = function() {
            $scope.refreshing = true;
            gamelobbylist.refresh();
        };

        // Joining. Joining a full lobby makes you a spectator.
        $scope.joinlobby = function(lobby) {
            gamelobbymanager.joinLobby(lobby.steamid);
        };

        // Get number of games. Results in a "menu:numgames" event.
        gamelobby.refreshnumgames();
    }

}

menuModule.controller('OnlineGamesController', OnlineGamesController);
