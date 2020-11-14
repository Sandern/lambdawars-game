'use strict';

import menuModule from './module';

class WorkshopController {
    /*@ngInject*/
    constructor($scope) {
		$scope.pageID = 'content';
		
    }

}

menuModule.controller('WorkshopController', WorkshopController);