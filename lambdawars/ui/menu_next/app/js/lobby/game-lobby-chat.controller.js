'use strict';

import lobbyModule from './module';

class GameLobbyChatController {
    /*@ngInject*/
    constructor($scope) {
        $scope.lobbychat = true;
    }

}

lobbyModule.controller('GameLobbyChatController', GameLobbyChatController);