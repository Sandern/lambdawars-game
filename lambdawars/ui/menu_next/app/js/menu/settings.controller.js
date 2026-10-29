'use strict';

import menuModule from './module';
import angular from 'angular';

// The settings of the game's option dialogs (video, brightness, sound, keyboard and mouse, key bindings
// and multiplayer). Python (menu/settings.py) reads and applies them by id. Rows are headers, selects,
// segmented buttons, switches, sliders, key bindings and actions. Options with a label are translated,
// options with a text are shown as they are.

var LEVELS = [
    {value: 0, label: 'ST_Low'},
    {value: 1, label: 'ST_Medium'},
    {value: 2, label: 'ST_High'},
];

var ANTIALIAS_NAMES = {
    '1:0': 'ST_None', '2:0': '2X MSAA', '4:0': '4X MSAA', '6:0': '6X MSAA', '4:2': '8X CSAA', '4:4': '16X CSAA',
    '8:0': '8X MSAA', '8:2': '16XQ CSAA',
};

var CATEGORIES = [
    {id: 'video', title: 'ST_Video', desc: 'Settings_Video_Desc', icon: 'monitor', rows: [
        {type: 'header', label: 'ST_Display'},
        {id: 'aspect', label: 'ST_AspectRatio', type: 'select', options: [
            {value: 0, label: 'ST_Aspect_Normal'},
            {value: 1, label: 'ST_Aspect_16_9'},
            {value: 2, label: 'ST_Aspect_16_10'},
        ]},
        {id: 'resolution', label: 'ST_Resolution', hint: 'ST_Resolution_Hint', type: 'select'},
        {id: 'displaymode', label: 'ST_DisplayMode', type: 'seg', options: [
            {value: 'fullscreen', label: 'ST_Fullscreen'},
            {value: 'windowed', label: 'ST_Windowed'},
            {value: 'noborder', label: 'ST_NoBorder'},
        ]},
        {id: 'lockmouse', label: 'ST_LockMouse', hint: 'ST_LockMouse_Hint', type: 'switch',
            disabled: function(values) { return values.displaymode === 'fullscreen'; }},
        {id: 'filmgrain', label: 'ST_FilmGrain', type: 'slider', min: 0, max: 3, step: 0.2},
        {type: 'header', label: 'ST_Advanced'},
        {id: 'antialias', label: 'ST_Antialias', hint: 'ST_Antialias_Hint', type: 'select'},
        {id: 'filtering', label: 'ST_Filtering', type: 'select', options: [
            {value: 0, label: 'ST_Bilinear'},
            {value: 1, label: 'ST_Trilinear'},
            {value: 2, label: 'ST_Anisotropic', suffix: ' 2X'},
            {value: 4, label: 'ST_Anisotropic', suffix: ' 4X'},
            {value: 8, label: 'ST_Anisotropic', suffix: ' 8X'},
            {value: 16, label: 'ST_Anisotropic', suffix: ' 16X'},
        ]},
        {id: 'vsync', label: 'ST_VSync', type: 'select', options: [
            {value: 'disabled', label: 'ST_Disabled'},
            {value: 'double', label: 'ST_DoubleBuffered'},
            {value: 'triple', label: 'ST_TripleBuffered'},
        ]},
        {id: 'multicore', label: 'ST_Multicore', type: 'switch'},
        {id: 'shader', label: 'ST_ShaderDetail', type: 'select', options: LEVELS.concat([{value: 3, label: 'ST_VeryHigh'}])},
        {id: 'effect', label: 'ST_EffectDetail', type: 'select', options: LEVELS},
        {id: 'model', label: 'ST_ModelDetail', type: 'select', options: LEVELS},
        {id: 'pagedpool', label: 'ST_PagedPool', type: 'select', options: LEVELS},
        {id: 'lighting', label: 'ST_Lighting', hint: 'ST_Lighting_Hint', type: 'seg', options: [
            {value: false, label: 'ST_LightingSimple'},
            {value: true, label: 'ST_LightingDeferred'},
        ]},
        {id: 'recommended', label: 'ST_Recommended', hint: 'ST_Recommended_Hint', type: 'action', action: 'ST_UseRecommended'},
    ]},
    {id: 'brightness', title: 'Settings_Brightness', desc: 'Settings_Brightness_Desc', icon: 'brightness', rows: [
        {id: 'gamma', label: 'Settings_Brightness', hint: 'ST_Brightness_Hint', type: 'slider', min: 1.6, max: 2.6, step: 0.1},
    ]},
    {id: 'sound', title: 'ST_Sound', desc: 'Settings_Sound_Desc', icon: 'sound', rows: [
        {id: 'volume', label: 'ST_GameVolume', type: 'slider', min: 0, max: 100, step: 5, unit: '%'},
        {id: 'music', label: 'ST_MusicVolume', type: 'slider', min: 0, max: 100, step: 5, unit: '%'},
        {id: 'speakers', label: 'ST_Speakers', type: 'select', options: [
            {value: 0, label: 'ST_Headphones'},
            {value: 2, label: 'ST_Speakers2'},
            {value: 4, label: 'ST_Speakers4'},
            {value: 5, label: 'ST_Speakers51'},
        ]},
        {id: 'soundquality', label: 'ST_SoundQuality', type: 'select', options: LEVELS},
        {id: 'captions', label: 'ST_Captions', type: 'seg', options: [
            {value: 'off', label: 'ST_Off'},
            {value: 'subtitles', label: 'ST_Subtitles'},
            {value: 'full', label: 'ST_FullCaptions'},
        ]},
        {id: 'ordersounds', label: 'ST_OrderSounds', hint: 'ST_OrderSounds_Hint', type: 'switch'},
        {id: 'language', label: 'ST_Language', hint: 'ST_Language_Hint', type: 'select'},
        {type: 'header', label: 'ST_VoiceChat', requires: 'voice'},
        {id: 'voice', label: 'ST_Voice', type: 'switch'},
        {id: 'voicestyle', label: 'ST_VoiceStyle', type: 'seg', disabled: voiceDisabled, options: [
            {value: 'pushtotalk', label: 'ST_PushToTalk'},
            {value: 'openmic', label: 'ST_OpenMic'},
        ]},
        {id: 'voicethreshold', label: 'ST_VoiceThreshold', hint: 'ST_VoiceThreshold_Hint', type: 'slider', min: 100, max: 2000, step: 100,
            disabled: function(values) { return !values.voice || values.voicestyle !== 'openmic'; }},
        {id: 'voicetransmit', label: 'ST_VoiceTransmit', type: 'slider', min: 0, max: 100, step: 10, unit: '%',
            disabled: function(values, settings) { return !values.voice || !settings.micvolumefound; }},
        {id: 'voicereceive', label: 'ST_VoiceReceive', type: 'slider', min: 0, max: 100, step: 5, unit: '%', disabled: voiceDisabled},
        {id: 'micboost', label: 'ST_MicBoost', type: 'switch', disabled: voiceDisabled},
        {id: 'testmicrophone', label: 'ST_TestMicrophone', hint: 'ST_TestMicrophone_Hint', type: 'action', action: 'ST_TestMicrophone',
            disabled: voiceDisabled},
    ]},
    {id: 'input', title: 'ST_KeyboardMouse', desc: 'Settings_KeyboardMouse_Desc', icon: 'mouse', rows: [
        {id: 'sensitivity', label: 'ST_MouseSensitivity', type: 'slider', min: 1, max: 20, step: 0.5},
        {id: 'reversemouse', label: 'ST_ReverseMouse', type: 'switch'},
        {id: 'mousefilter', label: 'ST_MouseFilter', type: 'switch'},
        {id: 'console', label: 'ST_Console', type: 'switch'},
    ]},
    // Rows from the key list of the game, see buildKeyRows
    {id: 'keys', title: 'ST_KeyBindings', desc: 'ST_KeyBindings_Desc', icon: 'keyboard', rows: []},
    {id: 'multiplayer', title: 'ST_Multiplayer', desc: 'Settings_Multiplayer_Desc', icon: 'users', rows: [
        {id: 'landiscovery', label: 'ST_LanDiscovery', type: 'switch'},
        {id: 'customcontent', label: 'ST_CustomContent', hint: 'ST_CustomContent_Hint', type: 'select', options: [
            {value: 'all', label: 'ST_AllowAll'},
            {value: 'nosounds', label: 'ST_NoSounds'},
            {value: 'none', label: 'ST_None'},
        ]},
        {id: 'colorblind', label: 'ST_ColorBlind', type: 'seg', options: [
            {value: 2, label: 'ST_Enabled'},
            {value: 1, label: 'ST_CrosshairOnly'},
            {value: 0, label: 'ST_Disabled'},
        ]},
        {id: 'instructor', label: 'ST_Instructor', type: 'switch'},
        {id: 'freelook', label: 'ST_FreeLook', type: 'switch'},
        {id: 'gore', label: 'ST_Gore', type: 'seg', options: [
            {value: 'high', label: 'ST_High'},
            {value: 'low', label: 'ST_Low'},
        ]},
    ]},
];

// Key binding tabs, with the commands of the game's key list (scripts/kb_act.lst). Strategy holds what the
// RTS uses: the movement keys pan the camera, +zoom and +lookspin rotate it, +speed (Shift) and +duck (Ctrl)
// are the order and selection modifiers. First person holds the Half-Life 2 keys of the legacy first person
// mode. Actions without a label use the label of the key list. A shared action is the command of a strategy
// action, so it has the same key. Commands of the key list without a place here go to the strategy tab.
var KEY_TABS = [
    {id: 'rts', title: 'ST_KeysStrategy', sections: [
        {title: 'ST_KeysCamera', actions: [
            {command: '+forward', label: 'ST_Key_PanUp'},
            {command: '+back', label: 'ST_Key_PanDown'},
            {command: '+moveleft', label: 'ST_Key_PanLeft'},
            {command: '+moveright', label: 'ST_Key_PanRight'},
            {command: '+zoom', label: 'ST_Key_RotateLeft'},
            {command: '+lookspin', label: 'ST_Key_RotateRight'},
            'cam_reset',
        ]},
        {title: 'ST_KeysOrders', actions: [
            {command: '+speed', label: 'ST_Key_QueueOrders', hint: 'ST_Key_QueueOrders_Hint'},
            {command: '+duck', label: 'ST_Key_SelectionModifier', hint: 'ST_Key_SelectionModifier_Hint'},
        ]},
        {title: 'ST_KeysCommunication', actions: ['+voicerecord', 'say', 'say_team', '+status_players']},
        {title: 'ST_KeysGame', actions: ['jpeg', 'save quick', 'load quick', 'pause', 'toggleconsole',
            'incrementvar closecaption 0 1 1', 'quit']},
    ]},
    {id: 'fps', title: 'ST_KeysFirstPerson', badge: 'ST_KeysLegacy', sections: [
        {title: 'ST_KeysMovement', actions: [
            {command: '+forward', shared: true},
            {command: '+back', shared: true},
            {command: '+moveleft', shared: true},
            {command: '+moveright', shared: true},
            {command: '+speed', shared: true},
            {command: '+duck', shared: true},
            '+jump', '+walk', 'impulse 50',
        ]},
        {title: 'ST_KeysCombat', actions: ['+attack', '+attack2', '+reload', '+use', 'phys_swap', 'impulse 100']},
        {title: 'ST_KeysWeapons', actions: ['slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'invnext', 'invprev', 'lastinv']},
        {title: 'ST_KeysKeyboardLook', actions: ['+left', '+right', '+lookup', '+lookdown', '+moveup', '+movedown', '+strafe', '+klook']},
    ]},
];

function voiceDisabled(values) {
    return !values.voice;
}

// Names of the keys for the bind command, by KeyboardEvent.code and by keyCode
var KEY_CODES = {
    Space: 'SPACE', Enter: 'ENTER', Tab: 'TAB', Backspace: 'BACKSPACE', CapsLock: 'CAPSLOCK',
    ShiftLeft: 'SHIFT', ShiftRight: 'RSHIFT', ControlLeft: 'CTRL', ControlRight: 'RCTRL', AltLeft: 'ALT', AltRight: 'RALT',
    MetaLeft: 'LWIN', MetaRight: 'RWIN', ContextMenu: 'APP',
    ArrowUp: 'UPARROW', ArrowDown: 'DOWNARROW', ArrowLeft: 'LEFTARROW', ArrowRight: 'RIGHTARROW',
    Insert: 'INS', Delete: 'DEL', Home: 'HOME', End: 'END', PageUp: 'PGUP', PageDown: 'PGDN',
    Pause: 'PAUSE', ScrollLock: 'SCROLLLOCK', NumLock: 'NUMLOCK',
    Semicolon: 'SEMICOLON', Quote: '\'', Backquote: '`', Minus: '-', Equal: '=', BracketLeft: '[', BracketRight: ']',
    Backslash: '\\', Comma: ',', Period: '.', Slash: '/',
    Numpad0: 'KP_INS', Numpad1: 'KP_END', Numpad2: 'KP_DOWNARROW', Numpad3: 'KP_PGDN', Numpad4: 'KP_LEFTARROW',
    Numpad5: 'KP_5', Numpad6: 'KP_RIGHTARROW', Numpad7: 'KP_HOME', Numpad8: 'KP_UPARROW', Numpad9: 'KP_PGUP',
    NumpadDecimal: 'KP_DEL', NumpadDivide: 'KP_SLASH', NumpadMultiply: 'KP_MULTIPLY', NumpadSubtract: 'KP_MINUS',
    NumpadAdd: 'KP_PLUS', NumpadEnter: 'KP_ENTER',
};
var KEY_CODES_NUMERIC = {
    32: 'SPACE', 13: 'ENTER', 9: 'TAB', 8: 'BACKSPACE', 20: 'CAPSLOCK', 16: 'SHIFT', 17: 'CTRL', 18: 'ALT',
    38: 'UPARROW', 40: 'DOWNARROW', 37: 'LEFTARROW', 39: 'RIGHTARROW', 45: 'INS', 46: 'DEL', 36: 'HOME', 35: 'END',
    33: 'PGUP', 34: 'PGDN', 19: 'PAUSE', 145: 'SCROLLLOCK', 144: 'NUMLOCK', 186: 'SEMICOLON', 222: '\'', 192: '`',
    189: '-', 187: '=', 219: '[', 221: ']', 220: '\\', 188: ',', 190: '.', 191: '/', 106: 'KP_MULTIPLY', 107: 'KP_PLUS',
    109: 'KP_MINUS', 110: 'KP_DEL', 111: 'KP_SLASH',
};
var MOUSE_BUTTONS = ['MOUSE1', 'MOUSE3', 'MOUSE2', 'MOUSE4', 'MOUSE5'];

function keyName(event) {
    if( KEY_CODES[event.code] ) {
        return KEY_CODES[event.code];
    }
    var match = /^(?:Key|Digit)([A-Z0-9])$/.exec(event.code || '') || /^(F[0-9]{1,2})$/.exec(event.code || '');
    if( match ) {
        return match[1];
    }
    var code = event.keyCode;
    if( (code >= 65 && code <= 90) || (code >= 48 && code <= 57) ) {
        return String.fromCharCode(code);
    }
    if( code >= 112 && code <= 123 ) {
        return 'F' + (code - 111);
    }
    return KEY_CODES_NUMERIC[code] || '';
}

class SettingsController {
    /*@ngInject*/
    constructor($scope, $filter, $timeout, $interval, $document) {
        $scope.pageID = 'page';

        var translate = $filter('translate');
        var savedTimer = null;
        var micPoll = null;

        $scope.categories = CATEGORIES;
        $scope.category = CATEGORIES[0];
        $scope.loaded = false;
        $scope.settings = null;
        $scope.values = {};
        $scope.saved = {};
        $scope.listening = null;
        // Key bindings that lost their key to another action: {id: {key, action}}
        $scope.moved = {};
        $scope.keyTabs = [];
        $scope.keyTab = null;
        // Label of each key binding, on the strategy tab if it's on both
        var keyLabels = {};
        $scope.showSaved = false;
        $scope.restartNeeded = false;
        $scope.testingMicrophone = false;
        $scope.micLevel = 0;

        function translateOptions(options) {
            return options.map(function(option) {
                return {value: option.value, text: translate(option.label) + (option.suffix || '')};
            });
        }

        // The resolutions of the display mode and aspect ratio
        function updateResolutions() {
            var settings = $scope.settings;
            var modes = settings.resolutions[$scope.values.displaymode === 'fullscreen' ? 'fullscreen' : 'windowed'] || [];
            var aspectModes = modes.filter(function(mode) { return mode[2] === $scope.values.aspect; });
            $scope.options.resolution = (aspectModes.length ? aspectModes : modes).map(function(mode) {
                return {value: mode[0] + 'x' + mode[1], text: mode[0] + ' \u00d7 ' + mode[1], width: mode[0]};
            });
        }

        // Keeps a resolution of the list, the largest one not wider than the current resolution
        function pickResolution() {
            var options = $scope.options.resolution;
            if( !options.length || options.some(function(option) { return option.value === $scope.values.resolution; }) ) {
                return;
            }
            var width = parseInt($scope.values.resolution, 10) || 0;
            var fitting = options.filter(function(option) { return option.width <= width; });
            $scope.values.resolution = (fitting.length ? fitting[fitting.length - 1] : options[0]).value;
        }

        // The rows of the key binding tabs, from KEY_TABS and the actions of the game's key list
        function buildKeyRows(settings) {
            // Labels of the key list, the first one of a command listed twice
            var listLabels = {};
            settings.keys.forEach(function(section) {
                section.actions.forEach(function(action) {
                    if( !listLabels[action.command] ) {
                        listLabels[action.command] = action.label;
                    }
                });
            });
            var placed = {};
            keyLabels = {};

            function actionRow(entry) {
                var action = typeof entry === 'string' ? {command: entry} : entry;
                var id = 'key:' + action.command;
                var text = action.label ? translate(action.label) : listLabels[action.command];
                if( !(id in settings.values) ) {
                    return null;
                }
                placed[action.command] = true;
                if( !keyLabels[id] ) {
                    keyLabels[id] = text;
                }
                return {id: id, text: text, hint: action.hint || '', type: 'bind', command: action.command,
                    sharedWith: action.shared ? keyLabels[id] : ''};
            }

            $scope.keyTabs = KEY_TABS.map(function(tab) {
                var sections = tab.sections.map(function(section) {
                    return {title: section.title, rows: section.actions.map(actionRow).filter(Boolean)};
                });
                return {id: tab.id, title: tab.title, badge: tab.badge, sections: sections};
            });

            // Actions of the key list without a place on the tabs
            var other = [];
            settings.keys.forEach(function(section) {
                section.actions.forEach(function(action) {
                    if( !placed[action.command] ) {
                        other.push(actionRow(action.command));
                    }
                });
            });
            if( other.length ) {
                $scope.keyTabs[0].sections.push({title: 'ST_KeysOther', rows: other});
            }

            var allRows = [];
            $scope.keyTabs.forEach(function(tab) {
                tab.rows = [];
                tab.sections.filter(function(section) { return section.rows.length; }).forEach(function(section, i) {
                    tab.rows.push({type: 'header', label: section.title, hint: i === 0 ? 'ST_Keys_Hint' : ''});
                    tab.rows = tab.rows.concat(section.rows);
                });
                tab.count = tab.rows.filter(function(row) { return row.type === 'bind'; }).length;
                tab.rows.push({id: 'defaultkeys', label: 'ST_DefaultKeys', hint: 'ST_DefaultKeys_Hint', type: 'action', action: 'ST_UseDefaults'});
                allRows = allRows.concat(tab.rows);
            });
            $scope.keyTab = $scope.keyTabs[0];
            // Both tabs, for the unsaved changes of the category
            CATEGORIES.filter(function(category) { return category.id === 'keys'; })[0].rows = allRows;
        }

        $scope.selectKeyTab = function(tab) {
            stopListening();
            $scope.keyTab = tab;
            var rows = $document[0].querySelector('.st-rows');
            if( rows ) {
                rows.scrollTop = 0;
            }
        };

        $scope.isTabDirty = function(tab) {
            return tab.rows.some($scope.isDirty);
        };

        // The rows of the category, of the selected tab for the key bindings
        $scope.categoryRows = function() {
            return $scope.category.id === 'keys' ? $scope.keyTab.rows : $scope.category.rows;
        };

        // A hint, or where the key of a binding went, or the strategy action with the same key
        $scope.hintText = function(row) {
            var moved = $scope.moved[row.id];
            if( moved ) {
                return translate('ST_KeyMoved', {key: moved.key, action: moved.action});
            }
            if( row.sharedWith ) {
                return translate('ST_KeySharedHint', {action: row.sharedWith});
            }
            return row.hint ? translate(row.hint) : '';
        };

        function load() {
            gamesettings.get(function(settings) {
                $scope.$applyAsync(function() {
                    $scope.settings = settings;
                    var values = angular.copy(settings.values);
                    Object.keys(values).forEach(function(id) {
                        if( id.indexOf('key:') === 0 ) {
                            values[id] = values[id].toUpperCase();
                        }
                    });
                    $scope.values = values;
                    $scope.saved = angular.copy(values);

                    $scope.options = {};
                    CATEGORIES.forEach(function(category) {
                        category.rows.forEach(function(row) {
                            if( row.options ) {
                                $scope.options[row.id] = translateOptions(row.options);
                            }
                        });
                    });
                    $scope.options.antialias = settings.antialiasmodes.map(function(mode) {
                        var name = ANTIALIAS_NAMES[mode] || mode;
                        return {value: mode, text: name.indexOf('ST_') === 0 ? translate(name) : name};
                    });
                    $scope.options.language = settings.languages.map(function(language) {
                        return {value: language, text: language.charAt(0).toUpperCase() + language.slice(1)};
                    });
                    updateResolutions();
                    buildKeyRows(settings);
                    $scope.loaded = true;
                });
            });
        }
        load();

        // Rows
        $scope.isShown = function(row) {
            var available = $scope.settings.available;
            if( row.id === 'recommended' ) {
                return !!$scope.settings.recommended;
            }
            if( row.requires ) {
                return available[row.requires] !== false;
            }
            return !row.id || available[row.id] !== false;
        };

        $scope.isDisabled = function(row) {
            return !!row.disabled && row.disabled($scope.values, $scope.settings);
        };

        function isDirty(id) {
            return $scope.values[id] !== $scope.saved[id];
        }
        $scope.isDirty = function(row) {
            return !!row.id && row.type !== 'action' && isDirty(row.id);
        };

        $scope.isCategoryDirty = function(category) {
            return category.rows.some($scope.isDirty);
        };

        $scope.dirtyCategories = function() {
            if( !$scope.loaded ) {
                return [];
            }
            return CATEGORIES.filter($scope.isCategoryDirty);
        };

        $scope.dirtySummary = function() {
            return $scope.dirtyCategories().map(function(category) { return translate(category.title); }).join(', ');
        };

        $scope.selectCategory = function(category) {
            stopListening();
            $scope.category = category;
        };

        function changed() {
            $scope.showSaved = false;
        }

        $scope.set = function(row, value) {
            $scope.values[row.id] = value;
            $scope.changed(row);
        };

        $scope.changed = function(row) {
            if( row.id === 'aspect' || row.id === 'displaymode' ) {
                updateResolutions();
                pickResolution();
            }
            changed();
        };

        $scope.toggle = function(row) {
            $scope.set(row, !$scope.values[row.id]);
        };

        $scope.slide = function(row, value) {
            $scope.values[row.id] = Math.round(value * 100) / 100;
            changed();
        };

        $scope.formatSlider = function(row) {
            var value = Number($scope.values[row.id]);
            return value.toFixed(row.step < 1 ? 1 : 0) + (row.unit || '');
        };

        // Actions
        $scope.runAction = function(row) {
            if( row.id === 'recommended' ) {
                angular.extend($scope.values, $scope.settings.recommended);
                updateResolutions();
                changed();
            } else if( row.id === 'defaultkeys' ) {
                stopListening();
                var defaultkeys = $scope.settings.defaultkeys;
                Object.keys($scope.values).forEach(function(id) {
                    if( id.indexOf('key:') === 0 ) {
                        $scope.values[id] = (defaultkeys[id.slice(4)] || '').toUpperCase();
                    }
                });
                $scope.moved = {};
                changed();
            } else if( row.id === 'testmicrophone' ) {
                toggleMicrophoneTest();
            }
        };

        $scope.actionLabel = function(row) {
            if( row.id === 'testmicrophone' && $scope.testingMicrophone ) {
                return 'ST_StopTest';
            }
            return row.action;
        };

        // Microphone test, shows the input level
        function stopMicrophoneTest() {
            if( micPoll ) {
                $interval.cancel(micPoll);
                micPoll = null;
            }
            if( $scope.testingMicrophone ) {
                gamesettings.stopmicrophonetest();
            }
            $scope.testingMicrophone = false;
            $scope.micLevel = 0;
        }

        function toggleMicrophoneTest() {
            if( $scope.testingMicrophone ) {
                stopMicrophoneTest();
                return;
            }
            gamesettings.startmicrophonetest($scope.values.voicetransmit, function(started) {
                $scope.$applyAsync(function() {
                    if( !started ) {
                        return;
                    }
                    $scope.testingMicrophone = true;
                    micPoll = $interval(function() {
                        gamesettings.microphonelevel(function(level) {
                            $scope.$applyAsync(function() {
                                if( level < 0 ) {
                                    stopMicrophoneTest();
                                } else {
                                    $scope.micLevel = level;
                                }
                            });
                        });
                    }, 100);
                });
            });
        }

        // Key bindings: click a key, then press a key or mouse button. Escape cancels.
        function bindKey(key) {
            var id = $scope.listening;
            stopListening();
            if( !key ) {
                return;
            }
            // A key does one action, other actions lose it and say where it went
            Object.keys($scope.values).forEach(function(other) {
                if( other !== id && other.indexOf('key:') === 0 && $scope.values[other] === key ) {
                    $scope.values[other] = '';
                    $scope.moved[other] = {key: key, action: keyLabels[id]};
                }
            });
            $scope.values[id] = key;
            delete $scope.moved[id];
            changed();
        }

        function onKeyDown(event) {
            event.preventDefault();
            event.stopPropagation();
            $scope.$apply(function() {
                if( event.keyCode === 27 ) {
                    stopListening();
                } else {
                    bindKey(keyName(event));
                }
            });
        }

        function onMouseDown(event) {
            event.preventDefault();
            event.stopPropagation();
            $scope.$apply(function() {
                bindKey(MOUSE_BUTTONS[event.button] || '');
            });
        }

        function onWheel(event) {
            if( !event.deltaY ) {
                return;
            }
            event.preventDefault();
            $scope.$apply(function() {
                bindKey(event.deltaY < 0 ? 'MWHEELUP' : 'MWHEELDOWN');
            });
        }

        function onContextMenu(event) {
            event.preventDefault();
        }

        var document = $document[0];
        function stopListening() {
            if( !$scope.listening ) {
                return;
            }
            $scope.listening = null;
            document.removeEventListener('keydown', onKeyDown, true);
            document.removeEventListener('mousedown', onMouseDown, true);
            document.removeEventListener('wheel', onWheel, true);
            document.removeEventListener('contextmenu', onContextMenu, true);
        }

        $scope.listen = function(row) {
            if( $scope.listening ) {
                return;
            }
            $scope.listening = row.id;
            // After the click that started listening
            $timeout(function() {
                if( $scope.listening !== row.id ) {
                    return;
                }
                document.addEventListener('keydown', onKeyDown, true);
                document.addEventListener('mousedown', onMouseDown, true);
                document.addEventListener('wheel', onWheel, {capture: true, passive: false});
                document.addEventListener('contextmenu', onContextMenu, true);
            });
        };

        // Unsaved changes
        $scope.revert = function() {
            stopListening();
            $scope.values = angular.copy($scope.saved);
            $scope.moved = {};
            updateResolutions();
        };

        $scope.applying = false;
        $scope.apply = function() {
            if( $scope.applying ) {
                return;
            }
            stopListening();
            // As [id, value] pairs, objects reach Python as JS object handles instead of dictionaries
            var changes = [];
            Object.keys($scope.values).forEach(function(id) {
                if( isDirty(id) ) {
                    changes.push([id, $scope.values[id]]);
                }
            });
            $scope.applying = true;
            gamesettings.apply(changes, function(result) {
                $scope.$applyAsync(function() {
                    $scope.applying = false;
                    $scope.saved = angular.copy($scope.values);
                    $scope.moved = {};
                    $scope.restartNeeded = !!(result && result.restart);
                    $scope.showSaved = true;
                    if( savedTimer ) {
                        $timeout.cancel(savedTimer);
                    }
                    savedTimer = $timeout(function() {
                        $scope.showSaved = false;
                    }, $scope.restartNeeded ? 6000 : 2500);
                });
            });
        };

        // Brightness: three symbols, the left one should be barely visible
        $scope.calibration = function() {
            var gamma = $scope.values.gamma || 2.2;
            return [0.06, 0.18, 0.6].map(function(base) {
                return Math.min(1, base * (0.4 + (gamma - 1.6) / 0.6));
            });
        };

        $scope.$on('$destroy', function() {
            stopListening();
            stopMicrophoneTest();
            if( savedTimer ) {
                $timeout.cancel(savedTimer);
            }
        });
    }
}

menuModule.controller('SettingsController', SettingsController);

// Width of the slider thumb in pixels, see .st-slider in _pages.scss
var SLIDER_THUMB_WIDTH = 16;

// Range input that shows a value without writing back a value the browser adjusted to the step.
// Dragging is done here with mouse events, the browser of the game only moves the thumb on a click.
// Usage: <input type="range" settings-range="value" settings-change="slide($value)">
/*@ngInject*/
function settingsRange($document) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var input = element[0];
            var document = $document[0];

            function change(value) {
                scope.$apply(function() {
                    scope.$eval(attrs.settingsChange, {$value: value});
                });
            }

            // The value under the mouse, rounded to the step
            function setFromMouse(event) {
                var rect = input.getBoundingClientRect();
                var min = parseFloat(attrs.min), max = parseFloat(attrs.max), step = parseFloat(attrs.step) || 1;
                var ratio = (event.clientX - rect.left - SLIDER_THUMB_WIDTH / 2) / (rect.width - SLIDER_THUMB_WIDTH);
                ratio = Math.max(0, Math.min(1, ratio));
                var value = parseFloat((min + Math.round(ratio * (max - min) / step) * step).toFixed(4));
                if( value !== parseFloat(element.val()) ) {
                    element.val(value);
                    change(value);
                }
            }

            function onMouseMove(event) {
                event.preventDefault();
                setFromMouse(event);
            }

            function stopDragging() {
                document.removeEventListener('mousemove', onMouseMove, true);
                document.removeEventListener('mouseup', stopDragging, true);
            }

            element.on('mousedown', function(event) {
                if( event.button !== 0 || input.disabled ) {
                    return;
                }
                event.preventDefault();
                input.focus();
                setFromMouse(event);
                document.addEventListener('mousemove', onMouseMove, true);
                document.addEventListener('mouseup', stopDragging, true);
            });

            scope.$watch(attrs.settingsRange, function(value) {
                element.val(value);
            });
            // Keyboard
            element.on('input change', function() {
                change(parseFloat(element.val()));
            });
            scope.$on('$destroy', stopDragging);
        },
    };
}
menuModule.directive('settingsRange', settingsRange);
