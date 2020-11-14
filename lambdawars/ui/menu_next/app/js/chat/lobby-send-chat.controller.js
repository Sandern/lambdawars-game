'use strict';

import chatModule from './module';
import angular from 'angular';


class LobbySendChatController {
    /*@ngInject*/
    constructor($scope, $element, dropdownService) {
        var servicename = $element[0].attributes['chat-service'].value;
        var injector = angular.element(document.body).injector();
        var chatlobbyservice = injector.get(servicename);
        
        $scope.text = '';
        $scope.sendChat = function() {
            chatlobbyservice.sendChatMessage($scope.text);
            $scope.text = '';
            dropdownService.closeAll();
        };
    }

}

chatModule.controller('LobbySendChatController', LobbySendChatController);