'use strict';

import coreModule from './module';

/**
 * Stores persistent data between components.
 * @ngInject
 */
function gameService() {
	var GameService = function() {
		this.numcurplayers = 1;
		this.numgames = 0;
		this.usersteamid = undefined;
	};
	
	return new GameService();
}

coreModule.factory('gameservice', gameService);