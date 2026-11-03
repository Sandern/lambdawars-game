'use strict';

import coreModule from './module';

// The last mission and the last hosted game, shown on the home page. Kept in the browser
// storage of the menu, which persists between sessions (CEF cache folder).
var STORAGE_KEY = 'lambdawars.recent';

/*@ngInject*/
function recentService() {
    function load() {
        try {
            return JSON.parse(window.localStorage.getItem(STORAGE_KEY)) || {};
        } catch( e ) {
            return {};
        }
    }

    function save(data) {
        try {
            window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch( e ) {
            // Not remembered, the home page just doesn't show it
        }
    }

    return {
        lastMission: function() {
            return load().mission || null;
        },
        setLastMission: function(mapname, difficulty) {
            var data = load();
            data.mission = {mapname: mapname, difficulty: difficulty, time: Date.now()};
            save(data);
        },
        lastGame: function() {
            return load().game || null;
        },
        setLastGame: function(game) {
            var data = load();
            data.game = game;
            data.game.time = Date.now();
            save(data);
        },
    };
}

coreModule.factory('recent', recentService);
