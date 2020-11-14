'use strict';

import menuModule from './module';

class SettingsController {
    /*@ngInject*/
    constructor($scope) {
		$scope.pageID = 'content';
		
		$scope.video = function() { gameui.openvideo(); };
		$scope.brightness = function() { gameui.openbrightness(); };
		$scope.audio = function() { gameui.openaudio(); };
		$scope.keyboardmouse = function() { gameui.openkeyboardmouse(); };
		$scope.multiplayer = function() { gameui.openmultiplayersettings(); };
    }

}

menuModule.controller('SettingsController', SettingsController);