'use strict';

import matchesModule from './module';

/**
 * Displays the match history of a player.
 * @ngInject
 */
function MatchHistoryDirective(Restangular) {
    return {
        template: require('../../views/templates/match-history.html'),
        restrict: 'E',
        scope: {
            'steamid': '='
        },

        /*
        // optional compile function
        compile(tElement) {

        }
        */
        // optional link function
        link(scope) {
            scope.page = 1;
            scope.busy = false;

            var _currentlyShowing = {};

            scope.showMatchResult = function(match) {
                scope.showMatchUuid = match.match_uuid;
                console.log('Show match: ', scope.showMatchUuid);
            };

            scope.backToMatchHistory = function() {
                scope.showMatchUuid = undefined;
            };

            scope.nextPage = function() {
                if (!scope.matchHistory || scope.page >= (scope.matchHistory.total / scope.matchHistory.per_page)) {
                    return;
                }
                scope.page += 1;
            };
            scope.prevPage = function() {
                if (scope.page <= 1) {
                    return;
                }
                scope.page -= 1;
            };

            function updateMatchHistory() {
                if (!scope.steamid) {
                    return;
                }

                if (_currentlyShowing.steamid === scope.steamid && _currentlyShowing.page === scope.page) {
                    return;
                }

                _currentlyShowing.steamid = scope.steamid;
                _currentlyShowing.page = scope.page;

                console.log('Requesting history for: ', scope.steamid);
                scope.busy = true;
                Restangular.one('player/matches/list/'+scope.steamid+'/'+scope.page).get({per_page: 10})
                .then(function(response) {
                    console.log('matches response: ', response);
                    scope.busy = false;
                    scope.matchHistory = response;
                })
                .catch(function() {
                    scope.busy = false;
                });
            }

            scope.$watch('steamid', function(/*newValue, oldValue*/) {
                updateMatchHistory();
            });
            scope.$watch('page', function(/*newValue, oldValue*/) {
                updateMatchHistory();
            });
            updateMatchHistory();
        }
    };
}

matchesModule.directive('matchHistory',  MatchHistoryDirective);
