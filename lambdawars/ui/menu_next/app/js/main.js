'use strict';

import './app-pre-angular-logic';

import angular from 'angular';
import 'angular-sanitize';
import 'angular-animate';
import 'angular-route';
import 'angular-translate';
import 'ng-dialog';
import 'restangular';
import 'angular-chart.js';

// App
import './chat/_index';
import './core/_index';
import './menu/_index';
import './lobby/_index';
import './matches/_index';
import './matches/charts/_index';

require('../styles/main.scss');

function setup_low_res_support() {
    // Lazy fix for people with ant resolutions
    // To do it properly we would basically need to create a mobile UI, but don't care enough
    var body = angular.element(document.body);
    var win = angular.element(window);
    var startScalingSize = 1024; // Depends on our css!
    function onBodyResize(/*e*/) {
        if (win.clientWidth < startScalingSize) {
            var scaleFactor = win.clientWidth / startScalingSize;
            body.css('transform', 'scale('+win.clientWidth / startScalingSize+')');
            body.css('transform-origin', '0 0');
            body.css('height', 100 / scaleFactor + '%');
        } else {
            body.css('transform', '');
            body.css('transform-origin', '');
            body.css('height', '');
        }
    }

    win.on('resize', onBodyResize);
    onBodyResize();
}

// create and bootstrap application
function init_mainmenu(translations, ui_settings) {


    const requires = [
        'ngSanitize',
        'ngRoute',
        'ngAnimate',
        'pascalprecht.translate',
        'ngDialog',
        'restangular',
        'chart.js',

        // Our app
        'app.chat',
        'app.core',
        'app.menu',
        'app.lobby',
        'app.matches',
        'app.matches.charts'
    ];

    // mount on window for testing
    window.app = angular.module('app', requires);

    require('./app.controller');

    angular.module('app').constant('AppSettings',
        angular.merge(require('./constants'), ui_settings)
    );

    angular.module('app').config(require('./on_config'));

    angular.module('app').run(require('./on_run'));

    angular.bootstrap(document, ['app']);

    // Init app
    var injector = angular.element(document.body).injector();
    var chatlobby = injector.get('chatlobby');
    chatlobby.init(globalchat);

    var gamelobbymanager = injector.get('gamelobbymanager');
    gamelobbymanager.init(gamelobby);

    if( 'translationsDeferred' in window ) {
        var td = window.translationsDeferred;
        window.translationsDeferred = undefined;
        return td.resolve(translations);
    }

    setup_low_res_support();

}
window.init_mainmenu = init_mainmenu;
