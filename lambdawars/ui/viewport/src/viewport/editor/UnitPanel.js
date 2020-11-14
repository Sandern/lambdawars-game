import { ViewportElement } from '../ViewportElement';

//import 'jqwidgets-framework/jqwidgets/jqxgrid';
//import 'jqwidgets-framework/jqwidgets/jqxwindow';

export class UnitPanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		var element = this;
		
		// Theme
		var theme = 'wars';

		// Setup data
		this.units = this.config['units'];

		element.source =
		{
			localdata: this.getUnits(),
			datafields:
			[
				{ name: 'name', type: 'string' },
			],
			datatype: "array"
		};
		var dataAdapter = new $.jqx.dataAdapter(element.source);

		// Create the window and content
		this.content.jqxWindow({
			showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 200, maxWidth: 2000, maxHeight: 2000, height: 350, width: 200, theme: theme, autoOpen: false,
			initContent: function () {
			
				// Grid
				$(element.content).find("#unitpanel_unitGrid").jqxGrid(
				{
					width: '100%',
					height: '285px',
					source: dataAdapter,
					theme: theme,
					showfilterrow: true,
					filterable: true,
					columns: [
						{ text: 'Name', datafield: 'name', width: '100%', filtertype: 'textbox', filtercondition: 'contains' },
					],
					rowsheight : 17,
					pagerheight : 20,
					columnsheight : 20,
					selectionmode : 'singlerow', //'multiplerows',
				});
				
				// Place button
				$("#unitpanel_placeButton").jqxButton({ width: '100px', height: '20px', theme: theme});
				
				$('#unitpanel_placeButton').bind('click', function (/*event*/) {
					var rowindexes = $('#unitpanel_unitGrid').jqxGrid('getselectedrowindexes');
					if( rowindexes.length == 0 )
					{
						console.log('unit panel spawn: nothing selected');
						return;
					}
					var index = rowindexes[Math.floor(Math.random()*rowindexes.length)];
					var datarow = $("#unitpanel_unitGrid").jqxGrid('getrowdata', index);
			
					var playerdata = $("#unitpanel_playersDropdown").jqxDropDownList('getSelectedItem'); 
					var command = 'wars_abi ' + datarow['name'];
					if( playerdata.value != " " ) {
						command += ' owner=' + playerdata.value;
					}
						
					window['interface'].serverCommand(command);
				});
				
				// Dropdown players
				var source = [
					{ label : '-', value : ' ' },
					{ label : 'n', value : '0' },
					{ label : 'e', value : '1' },
					{ label : 'p1', value : '2' },
					{ label : 'p2', value : '3' },
					{ label : 'p3', value : '4' },
					{ label : 'p4', value : '5' },
					{ label : 'p5', value : '6' },
					{ label : 'p6', value : '7' },
					{ label : 'p7', value : '8' },
					{ label : 'p8', value : '9' },
					{ label : 'p9', value : '10' },
					{ label : 'p10', value : '11' },
					{ label : 'p11', value : '12' },
					{ label : 'p12', value : '13' },
				];
				// Create a jqxDropDownList
				$("#unitpanel_playersDropdown").jqxDropDownList({ source: source, width: '50px', height: '20px', selectedIndex: 0, enableBrowserBoundsDetection: true, theme: theme});
			}
		});
		
		// Use close event to update the visibility state
		this.content.on('close', function (/*event*/) 
		{ 
			element.obj.onSetVisible(false);
		});
		
		this.content.on('resizing', function (event) 
		{ 
			$("#unitpanel_unitGrid").jqxGrid('height', event.args.height - 40 - 25);
		});
		
		/*this.content.on('rowselect', function (event) 
		{ 
			if( !event.ctrlKey && !event.shiftKey )
			{
				$("#unitpanel_unitGrid").jqxGrid('clearselection');
			}
		}); */
		
		// Disable text selection
		//this.content.attr('unselectable', 'on')
		//	 .css('user-select', 'none')
		//	 .on('selectstart', false);
	}

	getUnits() {
		var data = new Array();
		
		this.units.sort();

		for (var i = 0; i < this.units.length; i++) {
			var row = {};
			
			row["name"] = this.units[i];
			data[i] = row;
		}

		return data;
	}

	setVisible(state) {
		if( this.content.is(":visible") == state )
			return;
			
		if( state ) {
			this.content.jqxWindow('open');
		}
		else {
			this.content.jqxWindow('close');
		}
	}

	clearList() {
		this.units = [];
		this.source.localdata = this.getUnits();
	}

	addUnit(name) {
		this.units.push(name);
		this.source.localdata = this.getUnits();
	}

	addUnits(names) {
		this.units.push.apply(this.units, names)
		this.source.localdata = this.getUnits();
	}

	// Listen to space key
	onSpacePressed() {
		var rowindexes = $('#unitpanel_unitGrid').jqxGrid('getselectedrowindexes');
		if( rowindexes.length == 0 )
		{
			console.log('unit panel spawn: nothing selected');
			return;
		}
		var index = rowindexes[Math.floor(Math.random()*rowindexes.length)];
		var datarow = $("#unitpanel_unitGrid").jqxGrid('getrowdata', index);
		
		var playerdata = $("#unitpanel_playersDropdown").jqxDropDownList('getSelectedItem'); 
		
		window['interface'].serverCommand('unit_create ' + datarow['name'] + ' ' + playerdata.value);
	}
}
