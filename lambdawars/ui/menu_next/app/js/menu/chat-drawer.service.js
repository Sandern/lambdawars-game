'use strict';

import menuModule from './module';
import angular from 'angular';

// Pages without a chat of their own open the global chat in a drawer, from the top bar
var DRAWER_PAGES = ['/Multiplayer', '/OnlineGames', '/Singleplayer', '/Missions'];
// The home page docks the chat, except on screens where there's no room for it
var DOCKED_CHAT_MIN_WIDTH = 1401;

/*@ngInject*/
function chatDrawerService($rootScope, $location, $window) {
    var drawer = {
        open: false,
    };

    drawer.available = function() {
        var path = $location.path();
        if( path === '/' ) {
            return $window.innerWidth < DOCKED_CHAT_MIN_WIDTH;
        }
        return DRAWER_PAGES.indexOf(path) !== -1;
    };

    drawer.toggle = function() {
        drawer.open = !drawer.open;
    };

    drawer.close = function() {
        drawer.open = false;
    };

    function closeIfUnavailable() {
        if( !drawer.available() ) {
            drawer.close();
        }
    }
    $rootScope.$on('$routeChangeSuccess', closeIfUnavailable);
    angular.element($window).on('resize', function() {
        $rootScope.$applyAsync(closeIfUnavailable);
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
