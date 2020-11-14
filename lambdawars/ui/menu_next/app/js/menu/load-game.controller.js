'use strict';

import menuModule from './module';

class LoadGameController {
    /*@ngInject*/
    constructor($scope, $routeParams, $location) {
		$scope.pageID = 'content';
		
        $scope.mode = $routeParams.mode;
        
        savedgames.getSavedGames(function(savedgames) {
            $scope.savedgames = savedgames;
            console.log('Got saved games: ', savedgames);
            $scope.$digest();
        });
        
        $scope.selectSavedGame = function(savefile) {
            $scope.selectedSavedGame = savefile;
        };
        
        $scope.loadgame = function() {
            console.log("Load selected game ", $scope.selectedSavedGame);
            savedgames.loadSavedGame($scope.selectedSavedGame);
        };
        
        $scope.savegame = function() {
            savedgames.saveGame($scope.selectedSavedGame !== 'NEW' ? $scope.selectedSavedGame : undefined);
            gameui.clientcommand('gameui_hide'); // go back ingame
            $location.path('/InGame');
        };
    }

}

menuModule.controller('LoadGameController', LoadGameController);