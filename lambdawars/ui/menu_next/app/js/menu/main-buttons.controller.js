'use strict';

import menuModule from './module';

// Pages belonging to each main menu section, used to highlight the active section
var SECTION_PAGES = {
    online: ['/Multiplayer', '/OnlineGames'],
    offline: ['/Singleplayer', '/Missions', '/LoadGame'],
    ingame: ['/InGame'],
    settings: ['/Settings'],
};

class MainButtonsController {
    /*@ngInject*/
    constructor($scope, $location, gamelobbymanager, chatdrawer) {
        $scope.chatdrawer = chatdrawer;

        $scope.quit = function() {
            gameui.clientcommand('quit');
        };

        $scope.isSection = function(section) {
            var path = $location.path();
            // The game lobby belongs to the section it was created from
            if( path === '/Gamelobby' ) {
                return section === (gamelobbymanager.isoffline ? 'offline' : 'online');
            }
            return SECTION_PAGES[section].indexOf(path) !== -1;
        };
    }

}

menuModule.controller('MainButtonsController', MainButtonsController);
