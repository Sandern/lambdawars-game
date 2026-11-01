import { ViewportElement } from '../../ViewportElement';

export class WaitingForPlayersPanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		this.title = null;
		this.bannerurl = null;
		this.bannercontent = null;
		this.motdurl = null;
		this.motdcontent = null;
		
		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	updateBanner(bannerurl) {
		if( this.bannerurl != bannerurl ) {
			this.bannerurl = bannerurl;
			
			const banner = $(this.content.find('#wars_waitingforplayers_banner'));
			banner.html('<div id="wars_waitingforplayers_banner"><iframe sandbox src="' + bannerurl + '" width="100%" height="100%" scrolling="no" seamless="seamless" frameBorder="0"></iframe></div>');
		}
	}

	updateBannerFromContent(bannercontent) {
		if( this.bannercontent === bannercontent ) {
			return;
		}
		this.bannercontent = bannercontent;
		const banner = $(this.content.find('#wars_waitingforplayers_banner'));
		banner.html(''); // Clear any old banner
		const bannercontainer = $('<div id="wars_waitingforplayers_banner"></div>')
		const banneriframe = $('<iframe sandbox width="100%" height="100%" scrolling="no" seamless="seamless" frameBorder="0"></iframe></div>');
		banneriframe.attr('srcdoc', bannercontent);
		bannercontainer.append(banneriframe);
		banner.append(bannercontainer);
	}

	updateMOTD(motdurl) {
		if( this.motdurl != motdurl ) {
			this.motdurl = motdurl;
			
			const banner = $(this.content.find('#wars_waitingforplayers_motd'));
			banner.html('<div id="wars_waitingforplayers_motd"><iframe sandbox src="' + motdurl + '" width="100%" height="100%" scrolling="no" seamless="seamless" frameBorder="0"></iframe></div>');
		}
	}

	updateMOTDFromContent(motdcontent) {
		if( this.motdcontent === motdcontent ) {
			return;
		}
		this.motdcontent = motdcontent;
		const motd = $(this.content.find('#wars_waitingforplayers_motd'));
		motd.html(''); // Clear any old motd
		const motdcontainer = $('<div id="wars_waitingforplayers_motd"></div>')
		const motdiframe = $('<iframe sandbox width="100%" height="100%" scrolling="no" seamless="seamless" frameBorder="0"></iframe></div>');
		motdiframe.attr('srcdoc', motdcontent);
		motdcontainer.append(motdiframe);
		motd.append(motdcontainer);
	}

	updatePanel(timeoutSeconds, title, gameplayers) {
		let playerlist, entry, countdownDiv;
		
		countdownDiv = $(this.content.find('#wars_waitingforplayers_countdown'));
		if( timeoutSeconds !== 0 ) {
			const timeoutDate = new Date();
			const timeoutTime = timeoutDate.getTime() + 1000 * timeoutSeconds; // Offset by one day;
			timeoutDate.setTime(timeoutTime);
			
			countdownDiv.show();
			countdownDiv.countdown(timeoutDate, function(event) {
				$(this).html(event.strftime('%M:%S'));
			});
		} else {
			countdownDiv.hide();
		}
		
		if( this.title !== title ) {
			this.title = title;
			const titlecontainer = $(this.content.find('#wars_waitingforplayers_lobbyname'));
			titlecontainer.html(title + ' ');
		}
		
		playerlist = $(this.content.find('#wars_waitingforplayers_playerlist'));
		playerlist.html('');
		
		for( let i = 0; i < gameplayers.length; i++ ) {
			const playerdata = gameplayers[i];
		
			entry = '<li>';
			
			entry += playerdata['playername'];
			entry += ' <span>- state: ' + playerdata['state'] + '</span>';
			
			entry += '</li>';
			playerlist.append($(entry));
		}
	}
}
