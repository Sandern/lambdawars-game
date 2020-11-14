'use strict';

import chartsModule from './module';

/**
 * Displays the resource spent chart of a single player, detailed per resource
 * cateogory.
 * @ngInject
 */
function resourcesSpentDetailChartDirective() {
    return {
        template: require('../../../views/templates/charts/resources-spent-detail.html'),
        restrict: 'E',
        scope: {
            matchData: '=',
            owner: '='
        },

        // optional link function
        link(scope) {
            var i, e, owner, value, resource, sampleStep;

            owner = scope.owner;

            // Line graph resources over time
            scope.resource_labels = [];
            scope.resource_series = [];
            scope.resource_data = [];
            scope.player_colours = ['#00FF00', 'FF0000', '#FFFF00', '#0000FF'];

            // Fixed categories for now
            var categories = ['economy', 'army', 'defense', 'technology'];

            scope.resource_series = categories;

            categories.forEach(function() {
                scope.resource_data.push([]);
            });

            // Calculate sample points
            sampleStep = Math.round(Math.max(1, scope.matchData.events.length / 25.0));

            function addSampleAt(idx) {
                e = scope.matchData.events[idx][owner];

                for (var catIdx = 0; catIdx < categories.length; catIdx++) {
                    var category = categories[catIdx];
                    value = 0;
                    for (resource in e.spent_resources_per_category) {
                        value += e.spent_resources_per_category[resource][category] || 0;
                    }

                    scope.resource_data[catIdx].push(value);
                }

                scope.resource_labels.push(Math.round(parseFloat(scope.matchData.events[idx].timestamp)));
            }

            for (i = 0; i < scope.matchData.events.length - 1; i = i + sampleStep) {
                addSampleAt(i);
            }
            addSampleAt(scope.matchData.events.length-1);

            scope.chart_options = {
                pointDot: false,
                bezierCurve: false,
                datasetFill : false,
                animation: false,
                legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<datasets.length; i++){%><li><span style=\"background-color:<%=datasets[i].strokeColor%>\"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>"
            };
        }
    };
}

chartsModule.directive('resourcesSpentDetailChart',  resourcesSpentDetailChartDirective);
