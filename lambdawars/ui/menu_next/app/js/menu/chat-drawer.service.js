'use strict';

import menuModule from './module';

// Pages without a chat of their own open the global chat in a drawer, from the top bar
var DRAWER_PAGES = ['/Multiplayer', '/OnlineGames', '/Missions'];

/*@ngInject*/
function chatDrawerService($rootScope, $location) {
    var drawer = {
        open: false,
    };

    drawer.available = function() {
        return DRAWER_PAGES.indexOf($location.path()) !== -1;
    };

    drawer.toggle = function() {
        drawer.open = !drawer.open;
    };

    drawer.close = function() {
        drawer.open = false;
    };

    $rootScope.$on('$routeChangeSuccess', function() {
        if( !drawer.available() ) {
            drawer.close();
        }
    });

    return drawer;
}
menuModule.factory('chatdrawer', chatDrawerService);

class ChatDrawerController {
    /*@ngInject*/
    constructor($scope, chatdrawer) {
        $scope.drawer = chatdrawer;
    }
}
menuModule.controller('ChatDrawerController', ChatDrawerController);
