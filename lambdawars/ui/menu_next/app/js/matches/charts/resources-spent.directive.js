'use strict';

import chartsModule from './module';

/**
 * Displays the resource spent chart of different players.
 * @ngInject
 */
function resourcesSpentChartDirective() {
    return {
        template: require('../../../views/templates/charts/resources-spent.html'),
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
            scope.player_colours = [];

            // Fixed categories for now
            var owner_to_index = {};

            for (owner in scope.matchData.players) {
                owner_to_index[owner] = scope.resource_series.length;
                scope.resource_series.push(scope.matchData.players[owner].name);
                scope.resource_data.push([]);
                scope.player_colours.push(scope.matchData.players[owner].color);
            }

            // Calculate sample points
            var sampleStep = Math.round(Math.max(1, scope.matchData.events.length / 25.0));

            function addSampleAt(idx) {
                var e = scope.matchData.events[idx];

                for (owner in e) {
                    if (!owner_to_index.hasOwnProperty(owner)) {
                        continue;
                    }

                    var owner_idx = owner_to_index[owner];

                    var value = 0;
                    for (var resource in e[owner].spent_resources) {
                        value += e[owner].spent_resources[resource] || 0;
                    }

                    scope.resource_data[owner_idx].push(value);
                }

                scope.resource_labels.push(Math.round(parseFloat(e.timestamp)));
            }

            for (var i = 0; i < scope.matchData.events.length - 1; i = i + sampleStep) {
                addSampleAt(i);
            }
            addSampleAt(scope.matchData.events.length-1);

            scope.chart_options = {
                pointDot: false,
                bezierCurve: false,
                legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<datasets.length; i++){%><li><span style=\"background-color:<%=datasets[i].strokeColor%>\"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>"
            };
        }
    };
}

chartsModule.directive('resourcesSpentChart',  resourcesSpentChartDirective);
