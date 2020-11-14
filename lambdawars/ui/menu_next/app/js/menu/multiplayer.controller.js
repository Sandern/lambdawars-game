'use strict';

import menuModule from './module';

class MultiplayerController {
    /*@ngInject*/
    constructor($scope) {
		$scope.pageID = 'content';
		
        // TEMPORARY (old gamelobby system)
        $scope.creategamelobby = function() {
            gameui.creategamelobby();
        };
        $scope.findpublicgame = function() {
            gameui.findpublicgame();
        };
        $scope.openserverbrowser = function() {
            gameui.clientcommand('openserverbrowser');
        };
    }

}

menuModule.controller('MultiplayerController', MultiplayerController);