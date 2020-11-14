import { ViewportElement } from '../../ViewportElement';

export class Objectives extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		var element = this;
		
		var n = 0;
		var f = 0;
		var s = 0;
		
		function runEffect() {
			const options = {};
			// run the effect
			$( "#wars_objectivespanel_objectivelist" ).toggle( "blind", options, 500 );
		}
		
		//--- Hide Button ---
		// Mouse Click
		$( "#wars_objectiv_button" ).click(function() {
			runEffect();
			//document.getElementById.('wars_objectiv_button').innerHTML ='<strong>Hello World</strong>';
			return false;
		});
		
		//Roll Over
		$( "#wars_objectiv_button" ).mouseover(function() {
			$('#wars_objectiv_button').attr('src','wars/objectives/frame_hide_over.png');
			return false;
		});

		//Mouse Out
		$( "#wars_objectiv_button" ).mouseout(function() {
			$('#wars_objectiv_button').attr('src','wars/objectives/frame_hide.png');
			return false;
		});
		//---END Hide Button---
		
		element.timers = [];
		
		element.clearObjectiveList = function()
		{
			var objectivelist = element.content.find('#wars_objectivespanel_objectivelist');
			objectivelist.html("");
			
			for( var i = 0; i < element.timers.length; i++ )
			{
				clearInterval(element.timers[i]);
			}
			element.timers = [];
		}

		element.rebuildObjectiveList = function(objectiveinfolist)
		{
			const options = {};

			let oldf=f;
			let olds=s;
			
			const objectivelist = $(element.content.find('#wars_objectivespanel_objectivelist'));
			
			// Clear old list
			element.clearObjectiveList();

			// And build new one
			for( let i = 0; i < objectiveinfolist.length; i++ )
			{
				const info = objectiveinfolist[i];
				const idString = "wars_objectivespanel_objectivelist_element"+i;
				// Setup new info
				let displayinfo = '';
				displayinfo +='<li id="'+idString+'" priority='+ info['priority']+' style="margin:5px; background-color: rgba(208, 130, 20, 0.2); border-radius: 5px;"> ';
				if(info['state']==0){
					n++;
					displayinfo += '<img src="wars/objectives/objective_box_normal.png" width="25" height="25" align="center" alt="point"/><font color="#FFFFFF" style="font-size:100%"><b class="normal">'
				}
				else if(info['state']==1){
					s++;
					displayinfo += '<img src="wars/objectives/objective_box_success.png" width="25" height="25" align="center" alt="point"/><font color="#00FF00" style="font-size:100%"><b class="success">'
				}
				else if(info['state']==2){
					f++;
					displayinfo += ' <img src="wars/objectives/objective_box_fail.png" width="25" height="25" align="center" alt="point"/><font color="#FF0000" style="font-size:100%"><b class="fail">'
				}
				else if(info['state']==3){
					n++;
					displayinfo += '<img src="wars/objectives/objective_box_normal.png" width="25" height="25" align="center" alt="point"/><font color="#FFFFFF" style="font-size:100%"><b class="normal">'
					
					var id = 'wars_objective_timer_' + i;
					var interval = setInterval(function() {
						var timeelement = document.getElementById(id);
						var timeleft = parseInt(timeelement.innerHTML) - 1
						timeelement.innerHTML = timeleft + ' | ';

						if (timeleft <= 0)
						{
							timeelement.innerHTML = '0 | ';
							clearInterval(interval);
						}
					}, 1000);
					element.timers.push(interval);
					
					displayinfo += '<span id="' + id + '">'+parseInt(info['timeleft'])+' | </span>';
				}
				else if(info['state']==4){
					n++;
					displayinfo += '<img src="wars/objectives/objective_box_normal.png" width="25" height="25" align="center" alt="point"/><font color="#FFFFFF" style="font-size:100%"><b class="normal">'
					
					var timeleft = parseInt(info['timeleft']);
					displayinfo += 'Timer Pauzed at ' + timeleft + ' | ';
				}
				
				displayinfo += info['description'];
				displayinfo += '</b></font></li>';
				//console.log('rebuildObjectiveList: ' + displayinfo);
				const entry = $(displayinfo);
				
				objectivelist.append(entry);
				
				$( "#"+idString ).effect( "highlight", options, 1000, callback );
			}
			
			// Set counts of In Progress, Failed and Completed objectives
			let numbercontainer = $(element.content.find('#wars_objectiv_normnum'));
			numbercontainer.html(n);
			numbercontainer = $(element.content.find('#wars_objectiv_sucnum'));
			numbercontainer.html(s);
			numbercontainer = $(element.content.find('#wars_objectiv_failnum'));
			numbercontainer.html(f);
			
			// Animate header picture when the succeeded or failed objectives count changed
			if(olds != s)
				$( "#wars_objectiv_sucnum" ).effect( "highlight", options, 1000, callback );
			if(oldf != f)
				$( "#wars_objectiv_failnum" ).effect( "highlight", options, 1000, callback );				
				
			n = 0;
			f = 0;
			s = 0;
		}

		function callback() {
		}
		
		// Setup
		const viewport = $('#viewport'); 
		const container = element.content.first();
		
		
		const vh = viewport.height()
		const vw = viewport.width()
		const scale =  vw/1600;
		
		container.css({'top': (vh*0.05)+'px'});
		container.css({'right': (vw*0.15)-(250)+'px'});
		
		console.log("right:" +((vw*0.05)+(500*scale))+"px  : width:"+500*scale  );
		container.css({'-webkit-transform': "scale("+scale+")"});
	}
}
