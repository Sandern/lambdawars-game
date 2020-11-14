'use strict';

import chartsModule from './module';

/**
 * Displays the resource collection over time for players.
 * @ngInject
 */
function resourceCollectionChartDirective() {
    return {
        template: require('../../../views/templates/charts/resource-collection.html'),
        restrict: 'E',
        scope: {
            matchData: '='
        },

        // optional link function
        link(scope) {
            var owner;

            // Bar graph total resources
            scope.labels = ['requisition'];
            scope.series = [];
            scope.data = [];
            for (owner in scope.matchData.collected_resources) {
                scope.series.push(scope.matchData.players[owner].name);

                scope.data.push([scope.matchData.collected_resources[owner].requisition]);
            }
        }
    };
}

chartsModule.directive('resourceCollectionChart',  resourceCollectionChartDirective);
