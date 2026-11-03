import { ViewportElement } from '../../ViewportElement';

// Base style for a server message given as html content, the frame doesn't get the styles of the hud
const MOTD_STYLE = '<style>body{margin:0;font-family:Arial,sans-serif;font-size:15px;line-height:1.5;color:#d9d6cf}p{margin:0}</style>';

const STATE_ICONS = {
	loading: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-9-9"/></svg>',
	connected: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
	disconnected: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
};
const STATE_LABELS = {
	loading: 'WFP_StateLoading',
	connected: 'WFP_StateReady',
	disconnected: 'WFP_StateDisconnected',
};

function escapeHtml(text) {
	return $('<div>').text(text === undefined || text === null ? '' : String(text)).html();
}

// The waiting for players panel: shown while the players load into a match. Updated every second by
// core/ui/waitingforplayers.py with the countdown, lobby name, players and the mode and map.
export class WaitingForPlayersPanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);

		this.motdurl = null;
		this.motdcontent = null;
		this.countdownEnd = null;

		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	translate(key, params) {
		const injector = angular.element(document.body).injector();
		return injector ? injector.get('$filter')('translate')(key, params) : key;
	}

	setMOTD(iframe) {
		const motd = $(this.content.find('#wars_waitingforplayers_motd'));
		motd.html('');
		motd.append(iframe);
		this.content.addClass('wfp-has-motd');
	}

	updateMOTD(motdurl) {
		if( this.motdurl === motdurl ) {
			return;
		}
		this.motdurl = motdurl;
		this.setMOTD($('<iframe sandbox scrolling="no" seamless="seamless" frameBorder="0"></iframe>').attr('src', motdurl));
	}

	updateMOTDFromContent(motdcontent) {
		if( this.motdcontent === motdcontent ) {
			return;
		}
		this.motdcontent = motdcontent;
		this.setMOTD($('<iframe sandbox scrolling="no" seamless="seamless" frameBorder="0"></iframe>').attr('srcdoc', MOTD_STYLE + motdcontent));
	}

	// timeoutSeconds: seconds until the match starts (anyway, while players are loading), 0 or less without countdown
	// title: lobby name, empty without lobby
	// gameplayers: [{playername, state (loading, connected, disconnected), team, iscpu, isyou, color}]
	// info: {mode, map}
	updatePanel(timeoutSeconds, title, gameplayers, info) {
		info = info || {};
		const content = this.content;
		const loading = gameplayers.filter((gp) => gp['state'] === 'loading').length;
		const ready = gameplayers.filter((gp) => gp['state'] === 'connected').length;
		const disconnected = gameplayers.length - loading - ready;

		content.toggleClass('wfp-starting', loading === 0);
		content.find('.wfp-eyebrow-text').text(this.translate(loading ? 'WFP_WaitingForPlayers' : 'WFP_Starting'));
		content.find('.wfp-title').text(title || this.translate('WFP_WaitText'));

		const subtitle = [info['mode'], this.teamSetup(gameplayers), info['map']].filter((part) => part);
		content.find('.wfp-subtitle').text(subtitle.join(' · '));

		this.updateCountdown(timeoutSeconds, loading > 0);

		let progress;
		if( loading ) {
			progress = loading === 1 ? this.translate('WFP_WaitingForOne') : this.translate('WFP_WaitingForMore', {count: loading});
		} else if( disconnected ) {
			progress = this.translate('WFP_PlayerDisconnected');
		} else {
			progress = this.translate('WFP_AllLoaded');
		}
		content.find('.wfp-progress-text').text(progress);
		content.find('.wfp-progress-count').text(ready + ' / ' + gameplayers.length);
		content.find('.wfp-progress-fill').css('width', (gameplayers.length ? Math.round(100 * ready / gameplayers.length) : 0) + '%');

		this.updatePlayers(gameplayers);
	}

	updateCountdown(timeoutSeconds, loading) {
		const timer = this.content.find('.wfp-timer');
		const countdown = this.content.find('.wfp-countdown');
		if( timeoutSeconds <= 0 ) {
			timer.hide();
			return;
		}
		timer.show();
		this.content.find('.wfp-timer-label').text(this.translate(loading ? 'WFP_StartsAnywayIn' : 'WFP_StartsIn'));

		const end = new Date(new Date().getTime() + 1000 * timeoutSeconds);
		countdown.countdown(end, function(event) {
			$(this).html(event.strftime('%M:%S'));
		});
	}

	// "2v2" for teams, nothing for free for all
	teamSetup(gameplayers) {
		const teams = this.groupTeams(gameplayers);
		if( teams.length < 2 ) {
			return '';
		}
		return teams.map((team) => team.players.length).join('v');
	}

	// Players by team, in team order. Team 0 and 1 (unassigned, spectators) are free for all.
	groupTeams(gameplayers) {
		const teams = {};
		gameplayers.forEach((gp) => {
			const team = gp['team'] > 1 ? gp['team'] : 0;
			(teams[team] = teams[team] || []).push(gp);
		});
		return Object.keys(teams).map(Number).sort((a, b) => a - b).map((team) => ({team: team, players: teams[team]}));
	}

	updatePlayers(gameplayers) {
		const teams = this.groupTeams(gameplayers);
		const list = this.content.find('#wars_waitingforplayers_playerlist');
		let html = '';
		teams.forEach((team, index) => {
			const header = teams.length > 1 ? this.translate('WFP_Team', {number: index + 1}) : this.translate('WFP_Players');
			html += '<div class="wfp-team"><h2>' + escapeHtml(header) + '</h2><ul>';
			team.players.forEach((gp) => {
				const state = STATE_ICONS[gp['state']] ? gp['state'] : 'loading';
				html += '<li class="wfp-player wfp-player-' + state + '">';
				html += '<span class="wfp-color"' + (gp['color'] ? ' style="background: ' + escapeHtml(gp['color']) + '"' : '') + '></span>';
				html += '<span class="wfp-name">' + escapeHtml(gp['playername']);
				if( gp['iscpu'] ) {
					html += '<span class="wfp-tag">' + escapeHtml(this.translate('WFP_Cpu')) + '</span>';
				}
				if( gp['isyou'] ) {
					html += '<span class="wfp-tag wfp-tag-you">' + escapeHtml(this.translate('WFP_You')) + '</span>';
				}
				html += '</span>';
				html += '<span class="wfp-state wfp-state-' + state + '">' + STATE_ICONS[state] + escapeHtml(this.translate(STATE_LABELS[state])) + '</span>';
				html += '</li>';
			});
			html += '</ul></div>';
		});
		list.html(html);
	}
}
