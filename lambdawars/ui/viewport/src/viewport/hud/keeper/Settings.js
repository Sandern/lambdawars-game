import { ViewportElement } from '../../ViewportElement';

import 'jquery-ui/ui/widgets/button';
import 'jquery-ui/ui/widgets/accordion';
import 'jquery-ui/ui/widgets/slider';

export class Settings extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		const element = this;
		
		// Setup container size: Scale width relative to viewport size, then fix up height to the desired aspect ratio
		const viewport = $('#viewport'); 
		const vh = viewport.height()

		const container = this.content.first();
		container.css({'width':vh*0.3+'px'});

		const hiddenPos = "-"+vh*0.25+"px";
		container.css({'right':hiddenPos});

		// Setup accordian
		const options = {
			clearStyle: true,
			autoHeight: false,
		}

		const settingsbutton = $('#swarmkeeper_settingsbutton');
		const settingspanel = $('#swarmkeeper_settingspanel');
		settingsbutton.button({
			icons: {
				primary: "ui-icon-carat-1-w",
			}
		});
		settingsbutton.css({'height':settingsbutton.width()+'px'});
		settingspanel.accordion( options );

		this.settingspanelhidden = true;
		settingsbutton.click( function() {
			if( element.settingspanelhidden == true ) {
				container.animate({right: '5px'}, 1000, "easeInOutQuad");
				element.settingspanelhidden = false;
			}
			else {
				container.animate({right: hiddenPos}, 1000, "easeInOutQuad");
				element.settingspanelhidden = true;
			}
			return false;
		} );

		// Setup slider interval
		$( "#swarmkeeper_slider_interval" ).slider({
			range: true,
			min: 0,
			max: 500,
			values: [ 120, 300 ],
			slide: function( event, ui ) {
				$( "#swarmkeeper_interval" ).val( ui.values[ 0 ] + " - " + ui.values[ 1 ] );
			},
			change: function(event/*, ui*/) {
				if(event.originalEvent==undefined) {
					return;
				}
				const min = $( "#swarmkeeper_slider_interval" ).slider( 'values', 0 );
				const max = $( "#swarmkeeper_slider_interval" ).slider( 'values', 1 );
				window['interface'].clientCommand('dk_set_marine_interval ' + min + ' ' + max);
			}
		});
		$( "#swarmkeeper_interval" ).val(  $( "#swarmkeeper_slider_interval" ).slider( "values", 0 ) +
			" - " + $( "#swarmkeeper_slider_interval" ).slider( "values", 1 ) );
			
		$( "#swarmkeeper_settings_spawnnow" ).button()
		$( "#swarmkeeper_settings_spawnnow" ).click( function() {
			window['interface'].clientCommand('dk_spawn_marines');
		} );

		// Setup creature max slider
		$( "#swarmkeeper_slidercreatures_max" ).slider({
			range: "min",
			min: 0,
			max: 200,
			value: 30,
			slide: function( event, ui ) {
				$( "#swarmkeeper_creatures_max" ).val( ui.value );
			},
			change: function(event/*, ui*/) {
				if(event.originalEvent==undefined) {
					return;
				}
				const limit = $( "#swarmkeeper_slidercreatures_max" ).slider( 'value' );
				window['interface'].clientCommand('sk_creature_limit ' + limit);
			}
		});
		$( "#swarmkeeper_creatures_max" ).val(  $( "#swarmkeeper_slidercreatures_max" ).slider( "value" ) );

		this.refreshSettings()
		
		// Disable text selection
		this.content.attr('unselectable', 'on')
				.css('user-select', 'none')
				.on('selectstart', false);
	}

	refreshSettings() {
		window['interface'].retrieveConVarValue('sk_marine_invade_interval_min', function(min) {
			$( "#swarmkeeper_slider_interval" ).slider( "values" , 0, min );
		} );
		window['interface'].retrieveConVarValue('sk_marine_invade_interval_max', function(max) {
			$( "#swarmkeeper_slider_interval" ).slider( "values" , 1, max );
		} );
	}
}
