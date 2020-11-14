'use strict';

/**
 * @ngInject
 */
function OnRun($templateCache) {
    $templateCache.put('confirmDisconnect', require('../views/dialogs/confirmdisconnect.html'));

    $templateCache.put('genericMsg', require('../views/dialogs/genericmsg.html'));
    $templateCache.put('kickMsg', require('../views/dialogs/kickdialog.html'));
    $templateCache.put('confirmKickMsg', require('../views/dialogs/confirmkick.html'));
    $templateCache.put('versionMismatch', require('../views/dialogs/versionmismatch.html'));
    $templateCache.put('genericMsg', require('../views/dialogs/genericmsg.html'));
}

module.exports = OnRun;