'use strict';

// "2vs2" is shown as "2v2", free for all stays "FFA"
export function teamSetupLabel(teamsetup) {
    if( !teamsetup ) {
        return '';
    }
    return teamsetup === 'FFA' ? teamsetup : teamsetup.replace(/vs/g, 'v');
}
