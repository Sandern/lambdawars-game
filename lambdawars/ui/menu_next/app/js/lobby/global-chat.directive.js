'use strict';

import lobbyModule from './module';

class GlobalChatDirective {
    /*@ngInject*/
    constructor() {
        this.template = require('../../views/templates/globalchat.html');
        this.restrict = 'A';
    }

    /*
    // optional compile function
    compile(tElement) {

    }

    // optional link function
    link(scope, element) {
        
    }*/
}

lobbyModule.directive('globalChat',  () => new GlobalChatDirective());