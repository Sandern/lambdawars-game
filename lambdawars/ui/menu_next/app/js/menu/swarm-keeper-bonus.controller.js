'use strict';

import menuModule from './module';

class SwarmKeeperBonusController {
    /*@ngInject*/
    constructor($scope, $location) {
        $scope.showSwarmBonus = $location.url() === '/';
        $scope.$on('$locationChangeSuccess', function(/*event*/){
            var url = $location.url();
            $scope.showSwarmBonus = url === '/';
        });
        
        $scope.launchSwarmKeeperBonus = function(/*event*/) {
            gameui.launchbonus();
        };
    }

}

menuModule.controller('SwarmKeeperBonusController', SwarmKeeperBonusController);
