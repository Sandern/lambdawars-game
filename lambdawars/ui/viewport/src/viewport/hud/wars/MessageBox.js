import { ViewportElement } from '../../ViewportElement';

export class MessageBox extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		var element = this;
		
		element.runEffect = function() {
			if(!smooth){
				element.obj.onClose();	
			}else{
				const options = {};
				//run the effect
				$( "#wars_messagebox_container" ).toggle( "blind", options, 500 );
				$( "#wars_messagebox_bg" ).toggle( "puff", options, 500 );
				setTimeout(function(){
						element.obj.onClose(); // Call into Python cef panel code - core/ui/messageboxdialog.py
				},500);	 
			}
		};
		
		
		//---Continue Button---
		// on click button
		$( "#wars_messagebox_container" ).click(function() {
			if(but_dis || look)
				return;
			element.runEffect();
			//document.getElementById.('wars_objectiv_button').innerHTML ='<strong>Hello World</strong>'
			return false;
		});

		//Roll Over
		$( "#wars_messagebox_container" ).mouseover(function() {
			if(but_dis || look)
				return;
			$('#wars_messagebox_button').attr('src','wars/messagebox/button_over.png');
			return false;
		});

		//Roll Out
		$( "#wars_messagebox_container" ).mouseout(function() {
			if(but_dis || look)
				return;
			$('#wars_messagebox_button').attr('src','wars/messagebox/button.png');
			return false;
		});
		//---END Continue Button---
		
		//Look continue button - triggered by code/entity - core/ui/messageboxdialog.py
		element.LookMessageBox = function(){
			look = true;
			$('#wars_messagebox_button').attr('src','wars/messagebox/button_disabled.png');
		}
		
		
		//Unlock continue button - triggered by code/entity - core/ui/messageboxdialog.py
		element.UnlockMessageBox = function(){
			look = false;
			if(!but_dis)
				$('#wars_messagebox_button').attr('src','wars/messagebox/button.png');
		}
		
			
		//Smooth Close - triggered by code/entity - core/ui/messageboxdialog.py
		element.SmoothCloseMessageBox = function(){
			smooth = true;
		}
		
		//Show text - triggered by code/entity
		element.MessageBoxText = function(text){
			if (typeof text == 'undefined') 
				return;
			$('#wars_messagebox_button').attr('src','wars/messagebox/button_disabled.png');
			$( "#wars_messagebox_container" ).fadeIn();
			$( "#wars_messagebox_bg" ).fadeIn();
			smooth = false;
			look = false;
			but_dis = true;
			if(text.length > 200){
				console.log(text.substr(199,200));
				boxText = text.substr(0,200)+"<br>"+text.substr(200,text.length);
			}else{
				boxText = text;
			}
			
			type(boxText,40);
		}

		// Show all text on click 
		$( "#wars_messagebox_container" ).click(function() {
			if(but_dis){
				but_dis = false;
				if(!look)
					$('#wars_messagebox_button').attr('src','wars/messagebox/button.png');
				clearTimeout(typing);
				var objectivelist = element.content.find('#wars_messagebox_text');
				objectivelist.html(boxText);
			}
			return false;
		});
		
		//type Effect
		function type(text,delay){
			var currentChar=1;
			var dest=document.getElementById("wars_messagebox_text");
			typing = setInterval(function(){
				if (dest){
				//console.log("Char"+currentChar);
				if (currentChar>text.length){
					//console.log("Inside");
					clearTimeout(typing)
					but_dis = false;
					if(!look)
						$('#wars_messagebox_button').attr('src','wars/messagebox/button.png');
					return;
				}
				dest.innerHTML=text.substr(0, currentChar);

				currentChar++
				}
			},delay);			
		}
		
		// Setup
		$( "#wars_messagebox_container" ).fadeOut();
		$( "#wars_messagebox_bg" ).fadeOut();
			

		//options
		var look = false;
		var but_dis = true;
		var smooth = false;
		
		//Type Effect
		var typing;
		var boxText = "";
	}

	setVisible(state) {
		super.setVisible(state);
		
		if( this.isVisible() ) {
			const container = this.content.first();
			const viewport = $('#viewport'); 

			// Get the viewport size (i.e. the player screen)
			const vh = viewport.height();
			const vw = viewport.width(); 
			
			const aspect = vh / vw;
			
			// Get the container size (i.e. the message box)
			const ch = container.height();
			const cw = container.width();
			//console.log('ch: ' + ch + ', cw: ' + cw);
			
			// Center the message box
			if(aspect == 0.75){
				container.css({'left': (vw*0.45)-(cw*0.5)+'px'});
				container.css({'top': (vh*0.65)-(ch*0.5)+'px'});
			}else{
				container.css({'left': (vw*0.5)-(cw*0.5)+'px'});
				container.css({'top': (vh*0.7)-(ch*0.5)+'px'});
			}
			container.css({'-webkit-transform': "scale("+vh/900+")"});
		}
	}
}
