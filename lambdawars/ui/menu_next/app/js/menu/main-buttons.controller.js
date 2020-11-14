'use strict';

import menuModule from './module';

class MainButtonsController {
    /*@ngInject*/
    constructor($scope) {
        $scope.quit = function() {
            gameui.clientcommand('quit');
        };
    }

}

menuModule.controller('MainButtonsController', MainButtonsController);
