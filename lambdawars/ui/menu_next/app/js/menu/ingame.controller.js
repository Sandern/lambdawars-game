'use strict';

import menuModule from './module';

class InGameController {
    /*@ngInject*/
    constructor($scope, ngDialog) {
		$scope.pageID = 'content';
		
        $scope.returntogame = function() {
            gameui.clientcommand('gameui_hide');
        };
        $scope.forfeit = function() {
            gameui.servercommand('player_forfeit');
            gameui.clientcommand('gameui_hide'); // go back ingame
        };
        $scope.disconnect = function() {
            if ($scope.ishosting && !$scope.isoffline && $scope.host_numplayers > 1) {
                // confirm leaving
                ngDialog.open({ 
                    template: 'confirmDisconnect', 
                    className: 'ngdialog-theme-wars',
                    showClose: true 
                }).closePromise.then(function (data) {
                    if (data.value) {
                        gameui.clientcommand('disconnect');
                    } else {
                        gameui.clientcommand('gameui_hide'); // go back ingame
                    }
                });
            } else {
                gameui.servercommand('player_forfeit');
                gameui.clientcommand('disconnect');
            }
        };
    }

}

menuModule.controller('InGameController', InGameController);