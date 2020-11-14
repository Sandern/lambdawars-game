'use strict';

import menuModule from './module';


class PlayerInfoController {
    /*@ngInject*/
    constructor($scope) {
        $scope.playername = '';
        $scope.hoursplayed = '127';
        $scope.avatarsrc = '';

        $scope.$on('user:name', function(event, playername) {
            $scope.playername = playername;
        });
        $scope.$on('user:steamid', function(event, steamid) {
            $scope.avatarsrc = "avatar://medium/" + steamid + '?' + new Date().getTime(); // Add date time to force reload when changed
        });
    }

}

menuModule.controller('PlayerInfoController', PlayerInfoController);
