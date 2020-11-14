const angular = require('angular');

/* Controllers */
var warsMain = angular.module('warsMain', []);

import { ViewportElement } from './viewport/ViewportElement';

// Editor
import { Toolbox } from './ui/editor/Toolbox';

// Sandbox panels
import { AbilityPanel } from './viewport/editor/AbilityPanel';
import { AttributePanel } from './viewport/editor/AttributePanel';
import { UnitPanel } from './viewport/editor/UnitPanel';

// Lambda Wars viewport
import { Chat } from './viewport/hud/wars/Chat';
import { MessageBox } from './viewport/hud/wars/MessageBox';
import { Objectives } from './viewport/hud/wars/Objectives';
import { Overrun } from './viewport/hud/wars/Overrun';
import { PlayerStatusPanel } from './viewport/hud/wars/PlayerStatusPanel';
import { PostGamePanel } from './viewport/hud/wars/PostGamePanel';
import { TopBar } from './viewport/hud/wars/TopBar';
import { WaitingForPlayersPanel } from './viewport/hud/wars/WaitingForPlayersPanel';

// Swarm Keeper ui 
import { Keeper } from './viewport/hud/keeper/Keeper';
import { Settings } from './viewport/hud/keeper/Settings';

let uiElementMap = {
	'viewport/ViewportElement': ViewportElement,

	'ui/editor/Toolbox': Toolbox,

	'viewport/editor/AbilityPanel': AbilityPanel,
	'viewport/editor/AttributePanel': AttributePanel,
	'viewport/editor/UnitPanel': UnitPanel,

	'viewport/hud/wars/Chat': Chat,
	'viewport/hud/wars/MessageBox': MessageBox,
	'viewport/hud/wars/Objectives': Objectives,
	'viewport/hud/wars/Overrun': Overrun,
	'viewport/hud/wars/PlayerStatusPanel': PlayerStatusPanel,
	'viewport/hud/wars/PostGamePanel': PostGamePanel,
	'viewport/hud/wars/TopBar': TopBar,
	'viewport/hud/wars/WaitingForPlayersPanel': WaitingForPlayersPanel,

	'viewport/hud/keeper/Keeper': Keeper,
	'viewport/hud/keeper/Settings': Settings,
};

warsMain.controller('ApplicationController', function($scope, $compile) {
	$scope.$on('insertElement', function(event, classidentifier, name, config) {
		if( classidentifier === '') {
			classidentifier = 'viewport/ViewportElement';
		}
		
		console.log( 'Loading element ' + name + ' (' + classidentifier + ')' );

		config['$compile'] = $compile;
		config['$scope'] = $scope;

		try {
			const element = new uiElementMap[classidentifier](name, config);
			window[name] = element;
			element.obj.onElementCreated(element, name);
			// Finalize loading
			element.initContent();
			element.setVisible(config['visible']);
			element.obj.onFinishedLoading();
			if( !$scope.$$phase ) {
				$scope.$digest();
			}
		} catch(e) {
			console.error('Could not create element ' + classidentifier + ':', e);
		}

	});
});




