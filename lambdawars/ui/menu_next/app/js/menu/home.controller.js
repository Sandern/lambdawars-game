'use strict';

import menuModule from './module';

class HomeController {
	/*@ngInject*/
    constructor($scope) {
		$scope.pageID = 'content';
    }

}

menuModule.controller('HomeController', HomeController);
