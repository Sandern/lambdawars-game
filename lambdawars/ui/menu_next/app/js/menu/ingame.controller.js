'use strict';

import menuModule from './module';

// The menu while playing (Escape). Whether the game is offline or hosted comes from user:ingame, the number of
// players of a hosted game from menu:host_numplayers (app.controller.js).
class InGameController {
    /*@ngInject*/
    constructor($scope) {
        $scope.pageID = 'page';
        // Lighter background, the game stays visible behind the menu
        $scope.pageClass = 'page-ingame';

        $scope.confirming = false;

        $scope.returntogame = function() {
            gameui.clientcommand('gameui_hide');
        };
        $scope.forfeit = function() {
            gameui.servercommand('player_forfeit');
            gameui.clientcommand('gameui_hide'); // go back ingame
        };
        // Hosting with other players connected ends the game for them too: confirm first
        $scope.leave = function() {
            if( $scope.ishosting && !$scope.isoffline && $scope.host_numplayers > 1 ) {
                $scope.confirming = true;
                return;
            }
            gameui.servercommand('player_forfeit');
            gameui.clientcommand('disconnect');
        };
        $scope.endGame = function() {
            gameui.clientcommand('disconnect');
        };
        $scope.cancelLeave = function() {
            $scope.confirming = false;
        };
    }

}

menuModule.controller('InGameController', InGameController);
