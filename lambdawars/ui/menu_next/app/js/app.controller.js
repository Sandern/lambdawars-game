'use strict';

import angular from 'angular';

/*@ngInject*/
function AppController($scope, $location, gameservice, gamelobbymanager, chatlobby, ngDialog, $translate) {
    // TODO: Split this up?
    $scope.ingame = false;
    $scope.steam_available = true;
    $scope.beta = 'default';
    $scope.numcurplayers = gameservice.numcurplayers;
    $scope.host_numplayers = 0;
    
    $scope.generalinfo = {
        numgames: gameservice.numgames
    };
    
    $scope.$on('steam:not_available', function(/*event*/) {
        $scope.steam_available = false;
        $translate('Steam_NotAvailable').then(function (translatedMsg) {
            ngDialog.open({ 
                template: 'genericMsg', 
                className: 'ngdialog-theme-wars',
                showClose: true,
                closeByDocument: false,
                data : {dialog_message: translatedMsg}
            });
        });
    });
    
    $scope.$on('menu:beta', function(event, beta, revision) {
        $scope.beta = beta;
        $scope.devrevision = revision;
    });
    
    $scope.$on('menu:numcurrentplayers', function(event, numcurplayers) {
        gameservice.numcurplayers = numcurplayers;
        $scope.numcurplayers = numcurplayers;
    });
    
    $scope.$on('menu:numgames', function(event, numgames) {
        gameservice.numgames = numgames;
        $scope.generalinfo.numgames = numgames;
    });
    
    $scope.$on('user:steamid', function(event, steamid) {
        gameservice.usersteamid = steamid;
    });
    
    $scope.$on('user:inputlanguage', function(event, localename) {
        $scope.inputlanguage = localename;
    });
    
    $scope.$on('user:ingame', function(event, ingame, ishosting, isoffline) {
        $scope.ishosting = ishosting;
        $scope.isoffline = isoffline;
        
        if( $scope.ingame !== ingame ) {
            $scope.ingame = ingame;
            chatlobby.ingameStateChanged(event, ingame, ishosting, isoffline);
            // For now, always change to the default page
            if( ingame ) {
                $location.path('/InGame');
            } else {
                if( gamelobbymanager.state === 'none' ) {
                    $location.path('/');
                } else {
                    $location.path('/Gamelobby');
                }
            }
        }
    });
    
    $scope.$on('menu:host_numplayers', function(event, numplayers) {
        $scope.host_numplayers = numplayers;
    });
    
    $scope.$on('user:kicked', function(/*event*/) {
        ngDialog.open({ 
            template: 'kickMsg', 
            className: 'ngdialog-theme-wars',
            showClose: true 
        });
    });
    
    $scope.$on('user:versionmismatch', function(/*event*/) {
        ngDialog.open({ 
            template: 'versionMismatch', 
            className: 'ngdialog-theme-wars',
            showClose: true 
        });
    });
    
    $scope.$on('show_generic_dialog', function(event, msg_translation_key) {
        $translate(msg_translation_key).then(function (translatedMsg) {
            ngDialog.open({ 
                template: 'genericMsg', 
                className: 'ngdialog-theme-wars',
                showClose: true,
                data : {dialog_message: translatedMsg}
            });
        });
    });
    
    //Play mouse over Sound
    /*$scope.soundCount=0;
    $scope.overSound = function(){
        angular.element('#button_over'+$scope.soundCount)[0].play();
        $scope.soundCount = ($scope.soundCount + 1) % 3;
    };*/
    
    // Get number of games. Results in a "menu:numgames" event.
    gamelobby.refreshnumgames();
}
angular.module('app')
	.controller('AppController', AppController);

