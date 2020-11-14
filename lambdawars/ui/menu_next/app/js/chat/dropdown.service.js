'use strict';

import chatModule from './module';

/**
 * @ngInject
 */
function dropdownService() {
    var openDropdows = [];

    return {
        getCounter: function () {
            return openDropdows.length;
        },
        areAllClosed: function() {
            return openDropdows.length === 0;
        },
        areAnyOpen: function() {
            return openDropdows.length !== 0;
        },
        open: function(item) {
            openDropdows.push(item);
        },
        close: function(item) {
            var index = openDropdows.indexOf(item);
            openDropdows.splice(index, 1);
        },
        closeAll: function(){
            for (var i = 0; i < openDropdows.length; i++) {
                openDropdows[i].closeDropdown();
            }
            openDropdows = [];
        }
    };
}

chatModule.factory('dropdownService', dropdownService);
