// Based on https://github.com/remind101/angular-tooltip

'use strict';

import coreModule from './module';
import angular from 'angular';
import Tether from 'tether';

var extend = angular.extend;

/*@ngInject*/
function tooltip() {
    // Default template for tooltips.
    var defaultTemplateUrl = 'template/ng-tooltip.html';
    this.setDefaultTemplateUrl = function(templateUrl) {
        defaultTemplateUrl = templateUrl;
    };

    var defaultTetherOptions = {
        attachment: 'top middle',
        targetAttachment: 'bottom middle'
    };
    this.setDefaultTetherOptions = function(options) {
        extend(defaultTetherOptions, options);
    };

    /*@ngInject*/
    this.$get = function($rootScope, $animate, $compile, $templateCache) {
      return function(options) {
        options = options || {};
        options = extend({ templateUrl: defaultTemplateUrl }, options);
        options.tether = extend({}, defaultTetherOptions, options.tether || {});

        var template = options.template || $templateCache.get(options.templateUrl),
            scope    = options.scope || $rootScope.$new(),
            target   = options.target,
            elem     = $compile(template)(scope),
            tether;

        /**
         * Attach a tether to the tooltip and the target element.
         */
        function attachTether() {
          tether = new Tether(extend({
            element: elem,
            target: target,
            attachment: 'top left',
            targetAttachment: 'bottom left',
            constraints: [
              {
                to: 'scrollParent',
                attachment: 'together',
                pin: true
              }
            ]
          }, options.tether));
          
          // Ensure position is right at start
          tether.position();
        }

        /**
         * Detach the tether.
         */
        function detachTether() {
          if (tether) {
            tether.destroy();
          }
        }

        /**
         * Open the tooltip
         */
        function open() {
          $animate.enter(elem, null, target);
          attachTether();
        }

        /**
         * Close the tooltip
         */
        function close() {
          $animate.leave(elem);
          detachTether();
        }

        // Close the tooltip when the scope is destroyed.
        scope.$on('$destroy', close);

        return {
          open: open,
          close: close
        };
      };
    };
}

coreModule.provider('$tooltip', tooltip);

/*@ngInject*/
function tooltipDirective() {
  /**
   * Returns a factory function for building a directive for tooltips.
   *
   * @param {String} name - The name of the directive.
   *
   * @ngInject
   */
  this.$get = function($tooltip) {
    return function(name, options) {
        return {
          restrict: 'EA',
          scope: {
            content:  '@' + name,
            tether:  '=?' + name + 'Tether'
          },
          link: function(scope, elem/*, attrs*/) {
            var tooltip = $tooltip(extend({
              target: elem,
              scope: scope
            }, options, { tether: scope.tether }));

            /**
             * Toggle the tooltip.
             */
            elem.bind("mouseenter", function(){
                tooltip.open();
            });
            elem.bind("mouseleave", function(){
                tooltip.close();
            });
          }
        };
      };
    };
}
coreModule.provider('$tooltipDirective', tooltipDirective);

/*@ngInject*/
function ngTooltip($tooltipDirective) {
    return $tooltipDirective('ngTooltip');
}
coreModule.directive('ngTooltip', ngTooltip);

/*@ngInject*/
function runTooltip($templateCache) {
    $templateCache.put('template/ng-tooltip.html', '<div class="tooltip">{{content}}</div>');
}
coreModule.run(runTooltip);