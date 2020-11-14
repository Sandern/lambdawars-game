'use strict';

import menuModule from './module';
import angular from 'angular';

class OnlineGamesController {
    /*@ngInject*/
    constructor($scope, gamelobbylist, gamelobbymanager) {
		$scope.pageID = 'content';
		
        $scope.lobbies = [];
        
        gamelobbylist.startUpdating(function() {
            if( !angular.equals($scope.lobbies, gamelobbylist.lobbies) ) {
                $scope.lobbies = gamelobbylist.lobbies;
                $scope.$digest();
            }
        });
        
        $scope.$on('$destroy', function iVeBeenDismissed() {
            gamelobbylist.stopUpdating();
        });
        
        $scope.joinlobby = function(steamid) {
            gamelobbymanager.joinLobby(steamid);
        };
        
        // Get number of games. Results in a "menu:numgames" event.
        gamelobby.refreshnumgames();
    }

}

menuModule.controller('OnlineGamesController', OnlineGamesController);