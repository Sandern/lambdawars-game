export class ViewportElement {
	constructor(name, config) {
		const element = this;
		
		// Dictionary provided by Python with configuration/initial values
		element.config = config;
			
		// Set object
		this.obj = window[name+'_obj'];

		// Load the list of css files
		this.obj.retrieveCSSFiles( function(cssfiles) {
			for (let i = 0; i < cssfiles.length; i++) {
				window['insertCss'](cssfiles[i]);
			}
		});
		
		// Load the html file
		const viewport = $('#viewport');
		const htmlcode = config['htmlcode'];
		this.content = $(config['$compile'](htmlcode)(config['$scope']));
		viewport.append(element.content);
	}

	// Called after construction and after replacing the complete html content (see replaceContent)
	initContent() {
	}

	toggleVisible(){
		const state = this.isVisible();
		this.setVisible( !state );
	}

	setVisible(state) {
		if( this.isVisible() === state )
			return;
			
		if( state ) {
			this.content.show();
		}
		else {
			this.content.hide();
		}
	}

	isVisible() {
		return this.content.is(":visible");
	}

	replaceContent(htmlcode) {
		this.content.html($(htmlcode));
		this.initContent();
	}

	onRemove () {
	
	}
}
