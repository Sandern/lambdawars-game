'use strict';

import lobbyModule from './module';

/*@ngInject*/
function badgesService($http, $q) {
    var deferred = $q.defer();
    $http.get('https://lambdawars.com/json/badges.json').then(function(res){

        // Temp hack. Json shouldn't contain image paths in the first place :(
        for (var badgeIdx = 0; badgeIdx < res.data.badges.length; badgeIdx++){
            res.data.badges[badgeIdx].image = res.data.badges[badgeIdx].image.replace('../mainmenu/', '../../mainmenu/');
        }

        deferred.resolve(res);
    }).catch(function (e) {
        console.error('Unable to retrieve badges: ', e);
        deferred.resolve({
            data: {
                badges: []
            }
        });
    });
    
    this.getBadges = function (){
        return deferred.promise;
    };
}

lobbyModule.service('badgesService', badgesService);