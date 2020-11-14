import { ViewportElement } from '../../ViewportElement';

export class PostGamePanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	updatePanel(winners, losers, type) {
		const titlebox = $(this.content.find('#wars_postgame_title'));
		if( type === 'won' ) {
			titlebox.html('You won the game!');
		} else if( type === 'lost' ) {
			titlebox.html('You lost the game!');
		} else {
			titlebox.html('Game ended.');
		}
		
		const winnersbox = $(this.content.find('#wars_postgame_winners'));
		winnersbox.html('Winners: ' + winners);
		const losersbox = $(this.content.find('#wars_postgame_losers'));
		losersbox.html('Losers: ' + losers);
	}
}
