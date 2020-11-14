'use strict';

/**
 * Import this file before importing angular!
 * Angular will use jQuery instead of jqLite when doing this.
 */
import jQuery from 'jQuery';
import _ from 'lodash';

window.jQuery = jQuery;
window.ngJq = 'jQuery';
window._ = _;