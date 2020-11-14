import { ViewportElement } from '../../ViewportElement';

import 'jquery-ui/ui/widgets/button';
import 'jquery-ui/ui/widgets/sortable';
import 'jquery-ui/ui/widgets/tabs';
import 'jquery-ui/ui/widgets/tooltip';

export class Keeper extends ViewportElement {
	constructor(name, config) {
		super(name, config);

		// Setup
		const viewport = $('#viewport'); 
		const container = this.content.first();
		const vh = viewport.height();
		container.css({'height':vh*0.3+'px'});
		const h = container.height() * 1.25;
		container.css({'width':h+'px'});

		this.setupTab('#swarmkeeper_spells');
		this.setupTab('#swarmkeeper_rooms');

		this.content.find( "#swarmkeeper_tabs" ).tabs();

		this.content.effect( 'slide', {}, 2500 );

		$('body').css('font-size', ((vh / 1080.0) * 100) + '%');
		
		// Enable JQuery UI tooltips on our content
		this.content.tooltip();
		
		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	setupTab(id) {
		const sortable = this.content.find(id);

		//sortable.resizable( );
		sortable.sortable( { grid: [0, 0] } );
		sortable.disableSelection();
	}

	clearList() {
		this.content.find('#swarmkeeper_spells').html("");
		this.content.find('#swarmkeeper_rooms').html("");
	}

	insertItem(info) {
		let button;
		const sortable = this.content.find(info['category']);
		
		if( info['costs'] )
			button = $('<li><button title="'+info['tooltip']+'">'+info['displayname']+' ('+info['costs']+')</button></li>');
		else
			button = $('<li><button title="'+info['tooltip']+'">'+info['displayname']+'</button></li>');
		
		const viewport = $('#viewport');
		const vh = viewport.height()
		//console.log('Viewport h: ' + viewport.height() + ' w: ' + viewport.width());
		
		button.css({'width':vh*0.075+'px'});
		button.css({'height':vh*0.075+'px'});
		
		button.find('button').button();
		button.find('button').disableSelection();

		const obj = this.obj;
		button.click(function() 
		{ 
			console.log('Clicked button: ' + info['name']);
			obj.onCommand(info['name']);
			return false; 
		});
		
		sortable.append( button );
		
		return button.find('button')
	}

	setGold(gold, maxgold) {
		const strgold = new String(gold);
		const strgoldmax = new String(maxgold);
		gold = $('#swarmkeeper_gold');
		gold.html('<b>Gold: ' + strgold + ' / ' + strgoldmax + '</b>')
	}
}
