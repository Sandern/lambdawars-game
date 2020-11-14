import { ViewportElement } from '../../ViewportElement';

export class Overrun extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		this.wavenumber = 0;
		this.waveprogress = 0.0;
	}

	initContent() {
		var readybutton = this.content.find('#wars_overrun_ready_button');
		var overrunElement = this;
		readybutton.click(function() {
			overrunElement.obj.onReady();
		});
	}

	onRemove() {
		super.onRemove(arguments);
		
		this.clearWaveCountdownTimer();
	}

	setVisible(state) {
		super.setVisible(state);
		
		if( this.isVisible() ) {
			const container = this.content.first();
			const viewport = $('#viewport'); 

			// Get the viewport size (i.e. the player screen)
			const vh = viewport.height();
			container.css({'-webkit-transform': "scale("+vh/900+")"});
			
			this.setNextWaveCountdown( 2, 15 ); // Testing
		}
	}

	hideReadyButton() {
		this.content.find('#wars_overrun_ready_button').animate({right: "-200px"}, 200).fadeOut();
		this.content.find('#wars_overrun_progress').show();
	}

	showReadyButton() {
		this.content.find('#wars_overrun_ready_button').show().animate({right: "0px"}, 200);
		this.content.find('#wars_overrun_progress').hide();
	}

	// Clears the wave count down timer if active
	clearWaveCountdownTimer() {
		if( this.countdowntimer ) {
			clearInterval(this.countdowntimer);
			this.countdowntimer = null;
		}
	}

	// Shows and starts countdown for next wave
	setNextWaveCountdown(wavenumber, nextwavetime) {
		this.wavenumber = wavenumber;
		this.wavetimecountdown = parseInt(nextwavetime);
		
		this.clearWaveCountdownTimer();
		if (this.wavetimecountdown <= 0) {
			this.setWaveActive(wavenumber);
			return;
		}
		
		this.showReadyButton();
		var id = 'wars_overrun_waveinfo';
		
		var overrunElement = this;
		this.countdowntimer = setInterval(function() {
			var timeelement = document.getElementById(id);
			overrunElement.wavetimecountdown -= 1;
			timeelement.innerHTML = 'Next wave in ' + overrunElement.wavetimecountdown + ' seconds! ';

			if (overrunElement.wavetimecountdown <= 0)
			{
				clearInterval(overrunElement.countdowntimer);
				overrunElement.countdowntimer = null;
				overrunElement.setWaveActive(overrunElement.wavenumber);
			}
		}, 1000);
	}

	// Sets wave as in progress
	setWaveActive(wavenumber) {
		this.wavenumber = wavenumber;
		this.hideReadyButton();
		var waveinfo = this.content.find('#wars_overrun_waveinfo');
		waveinfo.html('Wave ' + wavenumber + ' in progress!');
	}

	// Updates progress of the current wave
	updateWaveProgress(progress) {
		this.waveprogress = progress;
		var fullwidth = this.content.find('#wars_overrun_progress').width();
		this.content.find('#wars_overrun_progress_bar').css("width", (fullwidth*this.waveprogress) +"px");
		//console.log((fullwidth*this.waveprogress));
	}
}
