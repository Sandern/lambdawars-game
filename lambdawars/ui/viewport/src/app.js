const angular = require('angular');
require('angular-sanitize');
require('angular-translate');

import '../jqwidgets/jqx-all';

import './main';

var warsApp = angular.module("warsApp", ['pascalprecht.translate', 'warsMain'], function ($compileProvider) {
	// We use a custom protocol for loading steam avatar images
	$compileProvider.imgSrcSanitizationWhitelist(/^\s*((https?|ftp|mailto|steam|avatar|local|vtf):)|#/); 
});

warsApp.config(function ($translateProvider) {
	// Angular Translate 2.7:
	$translateProvider.useSanitizeValueStrategy(null);
	$translateProvider.useLoader('customLoader', {
		// if you have some custom properties, go for it!
	});
	$translateProvider.use('DONOTCARE');
});

warsApp.factory('customLoader', function ($http, $q) {
	// return loaderFn
	return function () {
		var deferred = $q.defer();
		if( 'interface' in window ) {
			window['interface'].gettranslations(function(data) {
				return deferred.resolve(data);
			});
		} else {
			window['translationsDeferred'] = deferred;
		}

		return deferred.promise;
	};
});

// This function is called by the game process after the js bindings are created
// Use this to initialize services which depend on those bindings
function init_viewport(translations) {
	angular.bootstrap(document, ['warsApp']);
	if( 'translationsDeferred' in window ) {
		var td = window['translationsDeferred'];
		window['translationsDeferred'] = undefined;
		return td.resolve(translations);
	}
}

window['init_viewport'] = init_viewport;
