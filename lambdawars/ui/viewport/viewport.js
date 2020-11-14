const $ = require('jquery');
require('jquery-ui/ui/disable-selection');
require('jquery-ui/ui/effect');
require('jquery-ui/ui/effects/effect-slide');
require('jquery-ui/ui/effects/effect-highlight');
require('jquery-countdown');

// export for others scripts to use
window['$'] = $;
window['jQuery'] = $;

// Add generic sort function for dom element
jQuery.fn.sortDomElements = (function() {
		return function(comparator) {
			return Array.prototype.sort.call(this, comparator).each(function() {
				this.parentNode.appendChild(this);
			});
		};
	})();

// Tell game process if the body element has focus or not. This way we can decide if key input should be processed in game.
$("body").focusin(function() {
	window['interface'].setCefFocus(true);
});

$("body").focusout(function() {
	window['interface'].setCefFocus(false);
});

require('./src/app');

// Helpers for setting up the viewport element
function insertElement(classidentifier, name, config)
{
	const $scope = angular.element('#app-container').scope();
	$scope.$apply(function() {
		$scope.$broadcast('insertElement', classidentifier, name, config);
	});
	
	return '';
}

function removeElement(name)
{
	console.log('Removing ' + name);
	const element = window[name];
	
	const viewport = $('#viewport');
	element.onRemove();
	viewport[0].removeChild( element.content[0] );
	
	delete element.content;
}

function getElement(name)
{
	return window[name];
}

function insertCss(cssfilename)
{
	// Should not exists yet
	const ss = document.styleSheets;
	for (let i = 0, max = ss.length; i < max; i++) {
		if (ss[i].href == cssfilename)
		{
			console.log('css file ' + cssfilename + ' already exists');
			return;
		}
	}
	
	// Create new link
	const headID = document.getElementsByTagName("head")[0];         
	const cssNode = document.createElement('link');
	cssNode.type = 'text/css';
	cssNode.rel = 'stylesheet';
	cssNode.href = cssfilename;
	headID.appendChild(cssNode);
	
	console.log('Loaded CSS: ' + cssfilename);
}

window.insertElement = insertElement;
window.removeElement = removeElement;
window.getElement = getElement;
window.insertCss = insertCss;

// jqWidgets
window.getTheme = function () {
	return 'wars';
}
