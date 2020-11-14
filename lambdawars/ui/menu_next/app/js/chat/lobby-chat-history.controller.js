'use strict';

import chatModule from './module';
import angular from 'angular';


class LobbyChatHistoryController {
    /*@ngInject*/
    constructor($scope, $element, $compile, $timeout, dropdownService) {
        var servicename = $element[0].attributes['chat-service'].value;
        var injector = angular.element(document.body).injector();
        var chatlobbyservice = injector.get(servicename);
        $scope.mutedusers = chatlobbyservice.mutedusers;
        $scope.chatHistory = chatlobbyservice.history;
        
        this.getChatLineStyle = function(type){
            if (type === 'global') {
                return {'color':'#80BFFF'};
            } else {
                if (type === 'admin') {
                    return {'color':'rgb(255,0,0)'};
                } else {
                    return {'color':'rgb('+ 207 +',' + 136+','+13+')'};
                }
            }
        };
        
        $scope.addChatLine = function(username, usersteamid, text, type) {
            //console.log(servicename + ' chat received line: ' + username + ': ' + text);
            $scope.chatHistory.push(
            {
                username: username,
                usersteamid: usersteamid,
                text: text,
                type: type,
            }
            );
            
            $element[0].scrollTop($element[0].scrollHeight);
        };
        
        $scope.muteUser = function(steamid) {
            chatlobbyservice.muteUser(steamid);
        };
        
        $scope.unmuteUser = function(steamid) {
            chatlobbyservice.unmuteUser(steamid);
        };
        
        $scope.isUserMute = function(steamid) {
            return chatlobbyservice.isUserMute(steamid);
        };
        
        $scope.isYourself = function(steamid) {
            return chatlobbyservice.isYourself(steamid);
        };
        
        $scope.$on(chatlobbyservice.broadcastname+':receivedline', function(/*event, username, usersteamid, text, type*/) {
            if (dropdownService.areAllClosed()) {
                $timeout(function(){
                    //I think this is ugly?
                    angular.element('#chat-messages').scrollTop(99999999);
                });
            }

        });
        //$element[0].scrollTop = $element[0].scrollHeight;
        angular.element('#chat-messages').scrollTop(99999999);
    }

}

chatModule.controller('LobbyChatHistoryController', LobbyChatHistoryController);