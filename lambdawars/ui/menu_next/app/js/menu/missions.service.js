'use strict';

import menuModule from './module';

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
    
    return missionsServiceInstance;
}

menuModule.factory('missions', missionsService);