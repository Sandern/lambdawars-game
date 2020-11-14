import { ViewportElement } from '../ViewportElement';

export class AbilityPanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);

		var element = this;
		
		// Theme
		var theme = 'wars';

		// Setup data
		this.abilities = this.config['abilities'];
		
		this.source =
		{
			localdata: this.getAbilities(),
			datafields:
			[
				{ name: 'name', type: 'string' },
			],
			datatype: "array"
		};
		var dataAdapter = new $.jqx.dataAdapter(this.source);

		// Create the window and content
		this.content.jqxWindow({
			showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 200, maxWidth: 2000, maxHeight: 2000, height: 350, width: 200, theme: theme, autoOpen: false,
			initContent: function () {
			
				// Grid
				$(element.content).find("#abilitypanel_abilityGrid").jqxGrid(
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
				$("#abilitypanel_executeButton").jqxButton({ width: '100px', height: '20px', theme: theme});
				
				$('#abilitypanel_executeButton').bind('click', function (/*event*/) {
					var index = $("#abilitypanel_abilityGrid").jqxGrid('getselectedrowindex');
					var datarow = $("#abilitypanel_abilityGrid").jqxGrid('getrowdata', index);
					window['interface'].serverCommand('wars_abi ' + datarow['name']);
				});
			}
		});

		// Use close event to update the visibility state
		this.content.on('close', function (/*event*/) 
		{ 
			element.obj.onSetVisible(false);
		});
		
		this.content.on('resizing', function (event) 
		{ 
			$("#abilitypanel_abilityGrid").jqxGrid('height', event.args.height - 40 - 25);
		}); 
	}

	getAbilities() {
		var data = new Array();
		
		this.abilities.sort();

		for (var i = 0; i < this.abilities.length; i++) {
			var row = {};
			
			row["name"] = this.abilities[i];
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
		this.abilities = [];
		this.source.localdata = this.getAbilities();
		//$("#abilitypanel_abilityGrid").jqxGrid('updatebounddata');
	}

	addAbility(name) {
		this.abilities.push(name);
		this.source.localdata = this.getAbilities();
		//$("#abilitypanel_abilityGrid").jqxGrid('updatebounddata');
	}

	addAbilities(names) {
		this.abilities.push.apply(this.abilities, names)
		this.source.localdata = this.getAbilities();
		//$("#abilitypanel_abilityGrid").jqxGrid('updatebounddata');
	}

	// Listen to space key
	onSpacePressed() {
		var rowindexes = $('#abilitypanel_abilityGrid').jqxGrid('getselectedrowindexes');
		if( rowindexes.length == 0 )
		{
			console.log('ability panel execute: nothing selected');
			return;
		}
		var index = rowindexes[Math.floor(Math.random()*rowindexes.length)];
		var datarow = $("#abilitypanel_abilityGrid").jqxGrid('getrowdata', index);

		window['interface'].serverCommand('wars_abi ' + datarow['name']);
	}
}