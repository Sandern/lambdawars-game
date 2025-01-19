'use strict';

import menuModule from './module';

class TutorialsController {
    /*@ngInject*/
    constructor($scope) {
		$scope.pageID = 'content';

        $scope.playtutorial = function(mission) {
            gameui.creategametutorial(mission);
        };
    }

}

menuModule.controller('TutorialsController', TutorialsController);
