'use strict';

import chartsModule from './module';

/**
 * Displays the units statistics of different players.
 * @ngInject
 */
function unitsChartDirective() {
    return {
        template: require('../../../views/templates/charts/units.html'),
        restrict: 'E',
        scope: {
            matchData: '='
        },

        // optional link function
        link(/*scope*/) {

        }
    };
}

chartsModule.directive('unitsChart',  unitsChartDirective);
