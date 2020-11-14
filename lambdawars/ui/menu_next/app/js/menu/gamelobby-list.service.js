'use strict';

import menuModule from './module';

/*@ngInject*/
function gamelobbylistService($rootScope, $timeout) {
    var updateInterval = 1000;
    var gamelobbyListService = {};
    gamelobbyListService.lobbies = [];
    gamelobbyListService.isUpdating = false;
    
    gamelobbyListService.startUpdating = function(fncallback) {
        console.log('Start updating online games list...');
        gamelobbyListService.isUpdating = true;
        gamelobbyListService.fncallback = fncallback;
        gamelobbyListService.update_lobbies_promise = $timeout(gamelobbyListService.doUpdate, updateInterval);
    };
    
    gamelobbyListService.doUpdate = function() {
        if( 'gamelobby' in window ) {
            gamelobby.listlobbies(function(lobbies) {
                if( gamelobbyListService.isUpdating ) {
                    gamelobbyListService.lobbies = lobbies;
                    gamelobbyListService.fncallback();
                    gamelobbyListService.update_lobbies_promise = $timeout(gamelobbyListService.doUpdate, updateInterval);
                }
            });
        } else {
            // try again later
            gamelobbyListService.update_lobbies_promise = $timeout(gamelobbyListService.doUpdate, updateInterval);
        }
    };
    
    gamelobbyListService.stopUpdating = function() {
        if( gamelobbyListService.isUpdating ) {
            console.log('Stop updating online games list.');
            gamelobbyListService.isUpdating = false;
            if( gamelobbyListService.update_lobbies_promise ) {
                $timeout.cancel(gamelobbyListService.update_lobbies_promise);
            }
            gamelobbyListService.update_lobbies_promise = undefined;
            gamelobbyListService.fncallback = undefined;
        }
    };
    
    return gamelobbyListService;
}

menuModule.factory('gamelobbylist', gamelobbylistService);