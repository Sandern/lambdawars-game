'use strict';

import lobbyModule from './module';

/*@ngInject*/
function badgesService($q) {
    var deferred = $q.defer();
    deferred.resolve({
        data: {
            badges: []
        }
    });
    
    this.getBadges = function (){
        return deferred.promise;
    };
}

lobbyModule.service('badgesService', badgesService);