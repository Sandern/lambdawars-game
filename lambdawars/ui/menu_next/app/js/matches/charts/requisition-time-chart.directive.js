'use strict';

import chartsModule from './module';

/**
 * Displays the resource collection over time for players.
 * @ngInject
 */
function requisitionTimeChartDirective() {
    return {
        template: require('../../../views/templates/charts/requisition-time.html'),
        restrict: 'E',
        scope: {
            matchData: '='
        },

        // optional link function
        link(scope) {
            var owner;

            // Line graph resources over time
            scope.resource_labels = [];
            scope.resource_series = [];
            scope.resource_data = [];

            var owner_to_index = {};

            for (owner in scope.matchData.players) {
                scope.resource_series.push(scope.matchData.players[owner].name);
                scope.resource_data.push([]);
                owner_to_index[owner] = scope.resource_series.length - 1;
            }

            for (var i in scope.matchData.events) {
                var e = scope.matchData.events[i];
                for (owner in e) {
                    if (!owner_to_index.hasOwnProperty(owner)) {
                        continue;
                    }

                    var idx = owner_to_index[owner];
                    var num = e[owner].current_resources.requisition;
                    if (!num) {
                        scope.resource_data[idx].push(scope.resource_data[idx].length > 0 ?
                            scope.resource_data[idx][scope.resource_data[idx].length-1] : 0);
                    } else {
                        scope.resource_data[idx].push(num);
                    }

                }

                scope.resource_labels.push(parseFloat(e.timestamp).toFixed(1));
            }
        }
    };
}

chartsModule.directive('requisitionTimeChart',  requisitionTimeChartDirective);
