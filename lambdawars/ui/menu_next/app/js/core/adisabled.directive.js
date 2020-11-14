'use strict';

import coreModule from './module';

class ADisabledDirective {
    /*@ngInject*/
    constructor() {
    }

    
    // optional compile function
    compile(tElement, tAttrs) {
        //Disable href, based on class
        tElement.on("click", function(e) {
            if (tElement.hasClass("disabled")) {
                e.preventDefault();
                return false;
            }
        });

        //Disable ngClick
        tAttrs.ngClick = ("ng-click", "!("+tAttrs.aDisabled+") && ("+tAttrs.ngClick+")");

        //Toggle "disabled" to class when aDisabled becomes true
        return function (scope, iElement, iAttrs) {
            scope.$watch(iAttrs.aDisabled, function(newValue) {
                if (newValue !== undefined ) {
                    iElement.toggleClass("disabled", newValue);
                }
            });
        };
    }
/*
    // optional link function
    link(scope, element) {
        
    }*/
}

coreModule.directive('aDisabled',  () => new ADisabledDirective());
