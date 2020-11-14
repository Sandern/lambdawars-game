import { ViewportElement } from '../../ViewportElement';

export class PlayerStatusPanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	clearPlayerList()
	{
		const playerlist = this.content.find('#wars_playerstatuspanel_playerlist');
		playerlist.html("");
		const game_playerlist = this.content.find('#wars_playerstatuspanel_gameplayerlist');
		game_playerlist.html("");
	}

	createPlayerEntry(playerinfo)
	{
		const playersteamid = playerinfo['steamid'];
		let displayplayerinfo = '';
		displayplayerinfo += '<li index=' + playerinfo['index']+'>'
		displayplayerinfo += '<img height="24" width="24" src="' + (playersteamid ? 'avatar://small/' + playersteamid : '../menu_next/build/images/steam-avatar-unknown.jpg') + '"/>';
		displayplayerinfo += playerinfo['name'];
		displayplayerinfo += '<span> - ping ' + playerinfo['ping'] + '</span>';
		if( playerinfo['team'] > 0 ) {
			displayplayerinfo += ' - team ' + playerinfo['team'];
		}
		displayplayerinfo += ' - ' + playerinfo['state'];
		displayplayerinfo += '</li>';
	
		const entry = $(displayplayerinfo);
		entry.css("color", playerinfo['color']);
		
		return entry;
	}

	updatePlayers(gameplayers, players)
	{
		let playerlist = $(this.content.find('#wars_playerstatuspanel_gameplayerlist'));
		
		playerlist.html("");
		
		for( let i = 0; i < gameplayers.length; i++ )
		{
			const playerinfo = gameplayers[i];
			playerlist.append(this.createPlayerEntry(playerinfo));
		}
		
		playerlist = $(this.content.find('#wars_playerstatuspanel_playerlist'));
		playerlist.html("");
		for( let i = 0; i < players.length; i++ )
		{
			const playerinfo = players[i];
			playerlist.append(this.createPlayerEntry(playerinfo));
		}
	}
}
