'use strict';

import matchesModule from './module';

/**
 * Displays the match result of a player.
 * @ngInject
 */
function MatchResultDirective(Restangular, $timeout) {
    return {
        template: require('../../views/templates/match-result.html'),
        restrict: 'E',
        scope: {
            'matchUuid': '='
        },

        /*
        // optional compile function
        compile(tElement) {

        }
        */
        // optional link function
        link(scope) {
            var matchFetchPromise, destroyed;

            destroyed = false;

            console.log('Showing match result for: ', scope.matchUuid);

            function _fetchMatchResult() {
                if (!scope.matchUuid) {
                    return;
                }

                Restangular.one('player/matches/get/'+scope.matchUuid).get({})
                .then(function(response) {
                    matchFetchPromise = null;

                    if (destroyed) {
                        return;
                    }

                    if (response.error_msg) {
                        matchFetchPromise = $timeout(_fetchMatchResult, 1000);
                        return;
                    }
                    //console.log('matches response: ', response);
                    scope.matchData = response;

                    var seconds = parseFloat(scope.matchData.duration);
                    scope.durationMinutes = Math.floor(seconds / 60.0);
                    scope.durationSeconds = Math.round(seconds % 60);

                    if (scope.durationMinutes < 10) {scope.durationMinutes = '0'+scope.durationMinutes;}
                    if (scope.durationSeconds < 10) {scope.durationSeconds = '0'+scope.durationSeconds;}
                });
            }

            scope.selectedChart = 'scores';

            scope.selectChart = function(chartType) {
                scope.selectedChart = chartType;
            };

            scope.$on('$destroy', function() {
                destroyed = true;
                
                if (matchFetchPromise) {
                    $timeout.cancel(matchFetchPromise);
                    matchFetchPromise = null;
                }
            });

            _fetchMatchResult();
        }
    };
}

matchesModule.directive('matchResult',  MatchResultDirective);
