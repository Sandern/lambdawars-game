'use strict';

import coreModule from './module';

// Line icons drawn on a 24x24 grid, coloured with the text color (currentColor).
// Usage: <wars-icon name="globe"></wars-icon>
var ICONS = {
    'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z"/>',
    'lock': '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    'leave': '<path d="M10 4H5v16h5"/><path d="M14 8l4 4-4 4"/><path d="M18 12H9"/>',
    'invite': '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-3.9 3.1-7 7-7s7 3.1 7 7"/><path d="M19 8v6M16 11h6"/>',
    'eye': '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    'check': '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    'arrow-right': '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
    'external': '<path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M18 14v6H4V6h6"/>',
    'chevron-down': '<path d="M6 9l6 6 6-6"/>',
    'chevron-left': '<path d="M15 6l-6 6 6 6"/>',
    'close': '<path d="M6 6l12 12M18 6L6 18"/>',
    'power': '<path d="M12 3v9"/><path d="M6.3 6.8a8 8 0 1 0 11.4 0"/>',
    'chat': '<path d="M4 5h16v11H9l-5 4z"/>',
    'discord': '<path d="M4 5h16v11H9l-5 4z"/><path d="M9 10h.01M15 10h.01"/>',
    'users': '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18.5 14.3c1.9.8 3 2.9 3 5.7"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'refresh': '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>',
    'arrow-left': '<path d="M19 12H5"/><path d="M11 6l-6 6 6 6"/>',
    'chevron-right': '<path d="M9 6l6 6-6 6"/>',
    'image': '<rect x="3" y="5" width="18" height="14" rx="1"/><circle cx="8.5" cy="10" r="1.5"/><path d="M21 16l-5-5-8 8"/>',
    'tutorial': '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v6"/>',
    'monitor': '<rect x="3" y="5" width="18" height="12"/><path d="M8 21h8M12 17v4"/>',
    'brightness': '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"/>',
    'sound': '<path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M16 9a4 4 0 0 1 0 6M18.5 6.5a7.5 7.5 0 0 1 0 11"/>',
    'mouse': '<rect x="6" y="3" width="12" height="18" rx="6"/><path d="M12 7v4"/>',
    'keyboard': '<rect x="3" y="6" width="18" height="12" rx="1"/><path d="M7 10h.01M11 10h.01M15 10h.01M8 14h8"/>',
    'info': '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><path d="M12 7.5v.01"/>',
    'wrench': '<path d="M15 4a5 5 0 0 0-4.6 6.9L4 17.3V20h2.7l6.4-6.4A5 5 0 0 0 20 9l-3 1-2-2 1-3z"/>',
};

/*@ngInject*/
function warsIcon() {
    return {
        restrict: 'E',
        template: function(element, attrs) {
            return iconSvg(attrs.name);
        },
        link: function(scope, element, attrs) {
            // Names from an expression, like name="{{ category.icon }}"
            attrs.$observe('name', function(name) {
                if( name && element.children().attr('class') !== 'icon icon-' + name ) {
                    element.html(iconSvg(name));
                }
            });
        },
    };
}

function iconSvg(name) {
    return '<svg class="icon icon-' + name + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        (ICONS[name] || '') + '</svg>';
}
coreModule.directive('warsIcon', warsIcon);
