'use strict';

import chartsModule from './module';

/**
 * Displays the scores of different players.
 * @ngInject
 */
function scoresChartDirective() {
    return {
        template: require('../../../views/templates/charts/scores.html'),
        restrict: 'E',
        scope: {
            matchData: '='
        },

        // optional link function
        link(scope) {
            var score, matchData;

            scope.scores = {};

            matchData = scope.matchData;

            function computeResourcesScore(owner) {
                var collectedResources = matchData.collected_resources[owner];

                score = 0;
                for (var resType in collectedResources) {
                    score += collectedResources[resType];
                }
                return Math.round(score*100);
            }

            function computeArmyScore(owner) {
                var spentResourcesPerCategory = matchData.spent_resources_per_category[owner];

                score = 0;
                for (var resType in spentResourcesPerCategory) {
                    score += spentResourcesPerCategory[resType].army || 0;
                }

                return score * 100;
            }

            function computeTechScore(owner) {
                var spentResourcesPerCategory = matchData.spent_resources_per_category[owner];

                score = 0;
                for (var resType in spentResourcesPerCategory) {
                    score += spentResourcesPerCategory[resType].technology || 0;
                }

                return score * 100;
            }

            for (var owner in matchData.players) {
                var playerInfo = matchData.players[owner];

                scope.scores[owner] = {
                    team: playerInfo.team,
                    name: playerInfo.name,

                    // Scores
                    resources: computeResourcesScore(owner),
                    army: computeArmyScore(owner),
                    technology: computeTechScore(owner)
                };

                scope.scores[owner].overview = (scope.scores[owner].resources +
                    scope.scores[owner].army + scope.scores[owner].technology);
            }
        }
    };
}

chartsModule.directive('scoresChart',  scoresChartDirective);
