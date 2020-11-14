'use strict';

import menuModule from './module';

class HomeController {
	/*@ngInject*/
    constructor($scope, $http, $sce) {
		$scope.pageID = 'content';

		$http.get('https://www.lambdawars.com/game/news2.php')
			.then(function(response) {
				$scope.news = $sce.trustAsHtml('<main>' + response.data + '</main>');
			})
			.catch(function(response) {
				$scope.news = $sce.trustAsHtml('<main><h1>Unable to retrieve latest news</h1></main>');
				console.error('Failed to fetch news: ', response.data);
			});
    }

}

menuModule.controller('HomeController', HomeController);
