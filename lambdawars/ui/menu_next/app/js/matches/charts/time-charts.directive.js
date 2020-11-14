'use strict';

import chartsModule from './module';

/**
 * Displays the selected time chart, so basically another container for charts.
 * @ngInject
 */
function timeChartDirective() {
    return {
        template: require('../../../views/templates/charts/time-charts.html'),
        restrict: 'E',
        scope: {
            matchData: '='
        },

        // optional link function
        link(scope) {
            scope.data = {
                selectedChart: 'resources_spent'
            };

            scope.resource_spent_detail_charts = {};
            for (var owner in scope.matchData.players) {
                scope.resource_spent_detail_charts[owner] = 'resource_spent_detail_' + owner;
            }
        }
    };
}

chartsModule.directive('timeCharts',  timeChartDirective);
