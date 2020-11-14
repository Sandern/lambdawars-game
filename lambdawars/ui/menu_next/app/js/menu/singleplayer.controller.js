'use strict';

import menuModule from './module';

class SingleplayerController {
    /*@ngInject*/
    constructor($scope) {
		$scope.pageID = 'content';

        $scope.playtutorial = function() {
            gameui.creategametutorial();
        };
    }

}

menuModule.controller('SingleplayerController', SingleplayerController);
