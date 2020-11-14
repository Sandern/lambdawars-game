'use strict';

import menuModule from './module';

class ProfileController {
    /*@ngInject*/
    constructor($scope, gameservice) {
        $scope.pageID = 'content';

        $scope.matchHistorySteamId = gameservice.usersteamid;
        $scope.$on('user:steamid', function(event, steamid) {
            $scope.matchHistorySteamId = steamid;
        });
    }

}

menuModule.controller('ProfileController', ProfileController);