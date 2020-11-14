import { ViewportElement } from '../../ViewportElement';

export class TopBar extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	resortButtons() {
		const container = this.content.first();

		container.children().sortDomElements((a,b) => {
			const akey = $(a).attr("sortkey");
			const bkey = $(b).attr("sortkey");
			if (akey == bkey) return 0;
			if (akey < bkey) return -1;
			if (akey > bkey) return 1;
		})
	}

	insertButton(name, text, imagepath, order, floatright) {
		let button;
		const cssclass = !floatright ? 'wars_topbar_button' : 'wars_topbar_button_right';
		if( imagepath == '' ) {
			button = $('<input type="button" class="'+cssclass+'" value="'+text+'" />');
		} else {
			button = $('<input type="image" class="'+cssclass+'" src="'+imagepath+'" value="'+text+'" />');
		}
		button.attr('sortKey', order);
		
		const container = this.content.first();
		container.append(button);
		
		const element = this;
		button.mousedown(function(e) {
			element.obj.onButtonPressed(name);
			e.preventDefault(); // Prevent browser taking focus
		});
		
		this.resortButtons();
	}
}
