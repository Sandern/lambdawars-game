'use strict';

import chatModule from './module';

class dropdownController {
    /*@ngInject*/
    constructor($scope, dropdownService) {
        $scope.isopen = false;

        $scope.openDropdown = function() {
            console.log('open dropdown');
            dropdownService.closeAll();
            $scope.isopen = true;
            dropdownService.open($scope);
        };

        $scope.closeDropdown = function() {
            $scope.isopen = false;
            dropdownService.close($scope);
        };
    }

}

chatModule.controller('dropdownController', dropdownController);
