'use strict';

import coreModule from './module';

/**
 * @ngInject
 */
function customLoader($http, $q) {
    // return loaderFn
    return function (/*options*/) {
        var deferred = $q.defer();
        if( 'gameui' in window ) {
            gameui.gettranslations(function(data) {
                return deferred.resolve(data);
            });
        } else {
            window.translationsDeferred = deferred;
        }

        return deferred.promise;
    };
}

coreModule.factory('customLoader', customLoader);