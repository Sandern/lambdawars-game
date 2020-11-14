'use strict';

/**
 * @ngInject
 */
function OnConfig($locationProvider, $compileProvider, $translateProvider, $routeProvider, RestangularProvider, AppSettings) {
    RestangularProvider.setBaseUrl(AppSettings.LAMBDAWARS_API_URL);

    $routeProvider
    .when('/', {
        template: require('../views/home.html'),
        controller: 'HomeController',
        resolve: {
        }
    })
    .when('/Multiplayer', {
        template: require('../views/multiplayer.html'),
        controller: 'MultiplayerController',
        resolve: {
            testGameLobbyActive: ['$q', '$location', 'gamelobbymanager', function($q, $location, gamelobbymanager) {
                var deferred = $q.defer();
                deferred.resolve();
                if (gamelobbymanager.state !== 'none') {
                    $location.path('/Gamelobby');
                }
                return deferred.promise;
            }]
        }
    })
    .when('/Singleplayer', {
        template: require('../views/singleplayer.html'),
        controller: 'SingleplayerController',
        resolve: {
        }
    })
    .when('/LoadGame', {
        template: require('../views/loadgame.html'),
        controller: 'LoadGameController',
        resolve: {
        }
    })
    .when('/Settings', {
        template: require('../views/settings.html'),
        controller: 'SettingsController',
        resolve: {
        }
    })
    .when('/Missions', {
        template: require('../views/missions.html'),
        controller: 'MissionsController',
        resolve: {
        }
    })
    .when('/Workshop', {
        template: require('../views/workshop.html'),
        controller: 'WorkshopController',
        resolve: {
        }
    })
    .when('/OnlineGames', {
        template: require('../views/onlinegames.html'),
        controller: 'OnlineGamesController',
        resolve: {
            testGameLobbyActive: ['$q', '$location', 'gamelobbymanager', function($q, $location, gamelobbymanager) {
                var deferred = $q.defer();
                deferred.resolve();
                if (gamelobbymanager.state !== 'none') {
                    $location.path('/Gamelobby');
                }
                return deferred.promise;
            }]
        }
    })
    .when('/Gamelobby', {
        template: require('../views/gamelobby.html'),
        controller: 'GamelobbyController',
        resolve: {
        }
    })
    .when('/InGame', {
        template: require('../views/ingame.html'),
        controller: 'InGameController',
        resolve: {
        }
    })
    .when('/Profile', {
        template: require('../views/profile.html'),
        controller: 'ProfileController',
        resolve: {
        }
    })
    //.otherwise({redirectTo: '/home'});
    ;


    $locationProvider.html5Mode(false);

    // Allowed protocols for hrefs
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|ftp|mailto|local):/);

    // We use a custom protocol for loading steam avatar images
    $compileProvider.imgSrcSanitizationWhitelist(/^\s*((https?|ftp|mailto|steam|avatar|local|vtf|data):)|#/);

    // https://docs.angularjs.org/guide/production
    $compileProvider.debugInfoEnabled(false);

    // Angular Translate 2.7: should use sanitize, but escapes some html
    //$translateSanitizationProvider.useStrategy('sanitize');
    $translateProvider.useSanitizeValueStrategy(null);
    $translateProvider.useLoader('customLoader', {
        // if you have some custom properties, go for it!
    });
    $translateProvider.use('DONOTCARE');

}

module.exports = OnConfig;
