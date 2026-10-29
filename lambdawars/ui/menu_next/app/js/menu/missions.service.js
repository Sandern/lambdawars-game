'use strict';

import menuModule from './module';

// Defaults of GetMissions in mainmenu.py when the map resource doesn't have them
var DEFAULT_NAME = 'Unknown map';
var DEFAULT_DESCRIPTION = 'No description';

/*@ngInject*/
function missionsService() {
    var missionsServiceInstance = {};
    
    missionsServiceInstance.missions = [];
    missionsServiceInstance.missions_index = 0;
    
    missionsServiceInstance.update = function(fncallback) {
        if( !('gameui' in window) ) {
            fncallback();
            return;
        }
        gameui.retrievemissions(function(missions) {
            missionsServiceInstance.missions = missions;
            fncallback();
        });
    };
    
    // What the menu shows of a mission
    missionsServiceInstance.describe = function(mission) {
        return {
            mapname: mission.mapname,
            title: mission.name && mission.name !== DEFAULT_NAME ? mission.name : mission.mapname,
            description: mission.description && mission.description !== DEFAULT_DESCRIPTION ? mission.description : '',
            image: mission.image || '',
            workshop: !!mission.workshop,
        };
    };

    missionsServiceInstance.difficultyLabel = function(difficulty) {
        difficulty = difficulty || 'normal';
        return 'Mission_' + difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
    };
    
    return missionsServiceInstance;
}

menuModule.factory('missions', missionsService);