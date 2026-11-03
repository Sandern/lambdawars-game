'use strict';

import menuModule from './module';
import { teamSetupLabel } from '../core/format';

/*@ngInject*/
function gamelobbylistService($rootScope, $timeout) {
    var defaultUpdateInterval = 1000;
    var gamelobbyListService = {};
    gamelobbyListService.lobbies = [];
    gamelobbyListService.isUpdating = false;
    gamelobbyListService.lastUpdate = null;

    gamelobbyListService.startUpdating = function(fncallback, updateInterval) {
        console.log('Start updating online games list...');
        gamelobbyListService.isUpdating = true;
        gamelobbyListService.fncallback = fncallback;
        gamelobbyListService.updateInterval = updateInterval || defaultUpdateInterval;
        gamelobbyListService.update_lobbies_promise = $timeout(gamelobbyListService.doUpdate, 0);
    };

    gamelobbyListService.doUpdate = function() {
        gamelobbyListService.update_lobbies_promise = undefined;
        if( 'gamelobby' in window ) {
            gamelobby.listlobbies(function(lobbies) {
                if( gamelobbyListService.isUpdating ) {
                    gamelobbyListService.lobbies = lobbies;
                    gamelobbyListService.lastUpdate = Date.now();
                    gamelobbyListService.fncallback();
                    if( !gamelobbyListService.update_lobbies_promise ) {
                        gamelobbyListService.update_lobbies_promise = $timeout(gamelobbyListService.doUpdate, gamelobbyListService.updateInterval);
                    }
                }
            });
        } else {
            // try again later
            gamelobbyListService.update_lobbies_promise = $timeout(gamelobbyListService.doUpdate, gamelobbyListService.updateInterval);
        }
    };

    // Updates the list right away, instead of at the next interval
    gamelobbyListService.refresh = function() {
        if( !gamelobbyListService.isUpdating ) {
            return;
        }
        if( gamelobbyListService.update_lobbies_promise ) {
            $timeout.cancel(gamelobbyListService.update_lobbies_promise);
        }
        gamelobbyListService.doUpdate();
    };

    // Pages pass their callback, so a page that is left doesn't stop the updates of the next page
    gamelobbyListService.stopUpdating = function(fncallback) {
        if( fncallback && fncallback !== gamelobbyListService.fncallback ) {
            return;
        }
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

    // What the lobby lists of the menu show of a lobby
    gamelobbyListService.describe = function(lobby) {
        var taken = parseInt(lobby.numtakenslots, 10) || 0;
        var total = parseInt(lobby.numslots, 10) || 0;
        var modename = lobby.modename || lobby.mode || '';
        var isOverrun = lobby.mode === 'overrun';
        return {
            steamid: lobby.steamid,
            name: lobby.name,
            map: lobby.map,
            mode: lobby.mode,
            modename: modename,
            modeLabel: isOverrun || !lobby.teamsetup ? modename : modename + ' · ' + teamSetupLabel(lobby.teamsetup),
            isOverrun: isOverrun,
            taken: taken,
            total: total,
            open: Math.max(0, total - taken),
            isFull: total > 0 && taken >= total,
            fill: total ? Math.round(100 * taken / total) : 0,
            overviewsrc: lobby.overviewsrc || '',
            mapinstalled: lobby.mapinstalled !== false,
            teams: lobby.teams || [],
        };
    };

    // Lobbies that still have room, the fullest first: those start soonest
    gamelobbyListService.waitingForPlayers = function(lobbies) {
        return lobbies.filter(function(lobby) { return !lobby.isFull; }).sort(function(a, b) {
            return (b.fill - a.fill) || (b.taken - a.taken);
        });
    };

    return gamelobbyListService;
}

menuModule.factory('gamelobbylist', gamelobbylistService);
