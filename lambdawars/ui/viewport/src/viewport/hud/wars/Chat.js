import { ViewportElement } from '../../ViewportElement';

const entityMap = {
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	'"': '&quot;',
	"'": '&#39;',
	"/": '&#x2F;'
};

export class Chat extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		var element = this;
		this.mode = 0;
		this.ignoreNextEnter = false;
		this.chatopen = false;
		
		var input = this.content.find('#wars_chat_input');
		input.keyup(function(event){
			if(event.keyCode == 13){
				if( element.ignoreNextEnter ) {
					element.ignoreNextEnter = false;
					return;
				}
				window['interface'].clientCommand((element.mode === 2 ? 'say_team ' : 'say ') + input[0].value);
				input[0].value = "";
				element.stopChatActiveMode();
			}
		});
		
		//send button
		this.content.find( "#wars_send_button" ).mousedown(function() {
			window['interface'].clientCommand('say ' + input[0].value);
			input[0].value = "";
			element.stopChatActiveMode();
		});
		this.content.find( "#wars_send_team_button" ).mousedown(function() {
			window['interface'].clientCommand('say_team ' + input[0].value);
			input[0].value = "";
			element.stopChatActiveMode();
		});

		//click outside
		$("#wars_chat_container").focusout(function() {
			element.stopChatActiveMode();
		});
		//hide it at start
		element.stopChatActiveMode();
	}

	startChat(mode, enterKeyDown, languageid) {
		this.mode = mode;
		if( enterKeyDown ) {
			this.ignoreNextEnter = true;
		}
		this.chatopen = true;
		// Show the chat input box
		let input = this.content.find('#wars_chat_input_container');
		input.show();
		
		//Show old chat
		var history = this.content.find('#wars_chat_history');
		history.css('overflow-y','auto');
		history.children().each(function() {
			//$( this ).removeClass('wars_chat_line_fade');
			$( this ).addClass('wars_chat_line_fade_on');
			//$( this ).css('opacity','100');
		});
		
		// Put key focus on it
		input = this.content.find('#wars_chat_input');
		input[0].focus();
		
		input[0].setAttribute('placeholder', '['+languageid+'] ' + (mode === 2 ? 'message (team)' : 'message'));
	}

	updateChatPlaceholder(languageid) {
		var input = this.content.find('#wars_chat_input');
		input[0].setAttribute('placeholder', '['+languageid+'] ' + (this.mode === 2 ? 'message (team)' : 'message'));
	}

	stopChatActiveMode() {
		this.chatopen = false;
		// Hide input box and fade chat
		var input = this.content.find('#wars_chat_input_container');
		
		// Hide old chat			
		var history = this.content.find('#wars_chat_history');
		history.css('overflow-y','hidden'); 
		history.children().each(function() {
			//$( this ).removeClass('wars_chat_line_fade').addClass('wars_chat_line_fade');
			$( this ).toggleClass('wars_chat_line_fade', true);
			$( this ).removeClass('wars_chat_line_fade_on');
			//$( this ).css('opacity','0');
		});
		
		input.hide();
	}

	escapeHtml(string) {
		return String(string).replace(/[&<>"'/]/g, function (s) {
			return entityMap[s];
		});
	}

	strip_tags(input) {
		var allowed = '<font><b><i>';
		var _self = this;
		allowed = (((allowed || '') + '')
			.toLowerCase()
			.match(/<[a-z][a-z0-9]*>/g) || [])
			.join(''); // making sure the allowed arg is a string containing only tags in lowercase (<a><b><c>)
		var tags = /<\/?([a-z][a-z0-9]*)\b[^>]*>/gi,
			commentsAndPhpTags = /<!--[\s\S]*?-->|<\?(?:php)?[\s\S]*?\?>/gi;
		return input.replace(commentsAndPhpTags, '')
			.replace(tags, function($0, $1) {
				return allowed.indexOf('<' + $1.toLowerCase() + '>') > -1 ? $0 : _self.escapeHtml($0);
			});
	}

	addSmileys(text){
		var mapObj = {
			'#star':'<img src="../mainmenu/smilies/star.png" />',
			'#st':'<img src="../mainmenu/smilies/star.png" />',
			'#rebel':'<img src="../mainmenu/smilies/rebel.png" />',
			'#r':'<img src="../mainmenu/smilies/rebel.png" />',
			'#combine':'<img src="../mainmenu/smilies/combine.png" />',
			'#c':'<img src="../mainmenu/smilies/combine.png" />',
			'#lambda':'<img src="../mainmenu/smilies/lambda.png" />',
			'#l':'<img src="../mainmenu/smilies/lambda.png" />',
			'#nui':'<img src="../mainmenu/smilies/nui.png" />',
			
			'#smile':'<img src="../mainmenu/smilies/smile.png" />',
			'#s':'<img src="../mainmenu/smilies/smile.png" />',
			'#sad':'<img src="../mainmenu/smilies/sad.png" />',
			'#ss':'<img src="../mainmenu/smilies/sad.png" />',
			'#bigsmile':'<img src="../mainmenu/smilies/bigsmile.png" />',
			'#bs':'<img src="../mainmenu/smilies/bigsmile.png" />',
			'#dead':'<img src="../mainmenu/smilies/dead.png" />',
			'#ds':'<img src="../mainmenu/smilies/dead.png" />',
			'#angry':'<img src="../mainmenu/smilies/angry.png" />',
			'#a':'<img src="../mainmenu/smilies/angry.png" />',
			'#stare':'<img src="../mainmenu/smilies/stare.png" />',
			'#sta':'<img src="../mainmenu/smilies/stare.png" />',
			'#cry':'<img src="../mainmenu/smilies/cry.png" />',
			
			'#no':'<img src="../mainmenu/smilies/no.png" />',
			'#yes':'<img src="../mainmenu/smilies/yes.png" />',
			'#ok':'<img src="../mainmenu/smilies/ok.png" />',
			'#go':'<img src="../mainmenu/smilies/go.png" />',
			'#gl':'<img src="../mainmenu/smilies/gl.png" />',
			'#hf':'<img src="../mainmenu/smilies/hf.png" />',
			'#gg':'<img src="../mainmenu/smilies/gg.png" />',
			
			'#headcrab':'<img src="../mainmenu/smilies/headcrab.png" />',
			'#hc':'<img src="../mainmenu/smilies/headcrab.png" />',
			'#cookie':'<img src="../mainmenu/smilies/cookie.png" />',
			'#coo':'<img src="../mainmenu/smilies/cookie.png" />',
			'#zzz':'<img src="../mainmenu/smilies/zzz.png" />',
			'#error':'<img src="../mainmenu/smilies/error.png" />',
			'#fire':'<img src="../mainmenu/smilies/fire.png" />',
			'#luck':'<img src="../mainmenu/smilies/luck.png" />',
			
			'#br':'<br/>'
		};
			
		text = text.replace(/(#star)\b|(#st)\b|(#rebel)\b|(#r)\b|(#combine)\b|(#c)\b|(#lambda)\b|(#l)\b|(#nui)\b|(#smile)\b|(#s)\b|(#sad)\b|(#ss)\b|(#bigsmile)\b|(#bs)\b|(#dead)\b|(#ds)\b|(#angry)\b|(#a)\b|(#stare)\b|(#sta)\b|(#cry)\b|(#no)\b|(#yes)\b|(#ok)\b|(#go)\b|(#gg)\b|(#gl)\b|(#hf)\b|(#gg)\b|(#headcrab)\b|(#hc)\b|(#cookie)\b|(#coo)\b|(#zzz)\b|(#error)\b|(#fire)\b|(#luck)\b|(#br)\b/gi, function(matched){
			return mapObj[matched];
		});
		return text;
	}

	printChat(playername, color, msg) {
		playername = this.escapeHtml(playername);
		msg = this.strip_tags(msg);
		msg = this.addSmileys(msg);
		// Print received chat from players
		var history = this.content.find('#wars_chat_history');
		var chatLine = $('<span class="wars_chat_line"><b><span style="color:'+color+'"; -webkit-text-fill-color: "'+color+'">' + playername + '</span>: ' + msg + '</b></span><br />');
		history.append(chatLine);
		history[0].scrollTop = history[0].scrollHeight; // Make sure it's scrolled down
		if (!this.chatopen)
			chatLine.toggleClass('wars_chat_line_fade', true);
	}

	printChatNotification(msg) {
		msg = this.strip_tags(msg);
		
		// Print server message
		var history = this.content.find('#wars_chat_history');
		var chatLine = $('<span class="wars_chat_line"><b>' + msg + '</b></span><br />');
		history.append(chatLine);
		history[0].scrollTop = history[0].scrollHeight; // Make sure it's scrolled down
		if (!this.chatopen)
			chatLine.toggleClass('wars_chat_line_fade', true);
	}
}
