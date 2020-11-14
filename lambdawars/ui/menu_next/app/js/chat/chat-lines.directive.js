'use strict';

import chatModule from './module';

/**
 * @ngInject
 */
function chatLines(){
    return {
        restrict: 'E',
        template: require('../../views/templates/chatlines.html')
    };
}
chatModule.directive('chatLines', chatLines);
