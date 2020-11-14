import { ViewportElement } from '../ViewportElement';

export class AttributePanel extends ViewportElement {
	constructor(name, config) {
		super(name, config);
		
		var element = this;
		
		this.grids = {};
		
		// Theme
		var theme = 'wars';

		// Setup data
		this.abilities = this.config['abilities'];
		
		// Create window
		this.source =
		{
			localdata: this.abilities,
			datafields:
			[
				{ name: 'name', type: 'string' },
			],
			datatype: "array"
		};
		var dataAdapter = new $.jqx.dataAdapter(this.source);
		
		// List of tabs with grid
		// Can get the grid element by appending the name to "attributepanel_grid"
		this.gridNames = [
			'Info',
			'Class',
			'Instance'
		];
		
		// Create the window and content
		this.content.jqxWindow({
			showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 200, maxWidth: 2000, maxHeight: 2000, height: 500, width: 700, theme: theme, autoOpen: false,
			initContent: function () {
				// Splitter
				$(element.content).find('#attributepanel_contentSplitter').jqxSplitter({ theme: theme, width: '100%', height: '100%', panels: [{ size: '25%', min: 100 }, {min: 200, size: '75%'}] });
				
				// Grid
				$(element.content).find("#attributepanel_grid").jqxGrid(
				{
					width: '100%',
					height: '100%',
					source: dataAdapter,
					theme: theme,
					sortable: true,
					showfilterrow: true,
					filterable: true,
					columns: [
						{ text: 'Name', datafield: 'name', width: '100%', filtertype: 'textbox', filtercondition: 'contains' },
					],
					rowsheight : 17,
					pagerheight : 20,
					columnsheight : 20,
					selectionmode : 'singlerow',
				});
				
				// Attribute tabs
				$(element.content).find("#attributepanel_contentTabs").jqxTabs({ theme: theme, animationType: 'fade', height: '100%' });
				
				// Create attribute grids for each tab
				for (var i = 0; i < element.gridNames.length; i++) {
					var gridName = element.gridNames[i];
					var grid = $(element.content).find("#attributepanel_grid"+gridName);
					grid.gridname = gridName;
				
					// Create a new adapter
					var contentsource =
					{
						localdata: new Array(),
						datafields:
						[
							{ name: 'attribute', type: 'string' },
							{ name: 'value', type: 'string' },
						],
						datatype: "array"
					};
					var adapter = new $.jqx.dataAdapter(contentsource);
					adapter.attributes = {} // Map for each access to entries
					adapter.contentsource = contentsource; // Not sure which property it gets set to, so just set my own...
					adapter.refreshtimeout = null;
					
					if( element.gridNames[i] == 'Info' )
					{
						adapter.getattributescmd = 'abiinfo_requestall'
						adapter.setattributecmd = 'abiinfo_setattr'
					}
					else if( element.gridNames[i] == 'Class' )
					{
						adapter.getattributescmd = 'classinfo_requestall'
						adapter.setattributecmd = 'classinfo_setattr'
					}
					else
					{
						adapter.getattributescmd = '';
						adapter.setattributecmd = '';
					}

					grid.jqxGrid(
					{
						width: '100%',
						height: '100%',
						source: adapter,
						theme: theme,
						sortable: true,
						showfilterrow: false,
						filterable: true,
						editable: true,
						columns: [
							{ text: 'Attribute', datafield: 'attribute', width: '50%', filtertype: 'textbox', filtercondition: 'contains', editable: false },
							{ text: 'Value', datafield: 'value', width: '50%', filterable: false },
						],
					});
					
					// Respond to cell edit changes
					grid.on('cellendedit', function (event) {
						var args = event.args;
						var rowIndex = args.rowindex;
						var cellValue = args.value;
						var oldValue = args.oldvalue;
						var grid = event.args.owner;
						
						if( cellValue == oldValue )
							return;
						
						var abirowindex = $('#attributepanel_grid').jqxGrid('getselectedrowindex');
						var datarow = $("#attributepanel_grid").jqxGrid('getrowdata', abirowindex);
						
						var adapter = grid.source;
						if( adapter.setattributecmd == '' )
							return;
						
						const attribute = adapter.contentsource.localdata[rowIndex]['attribute']
						window['interface'].serverCommand(adapter.setattributecmd + ' ' + datarow['name'] + ' ' + attribute + ' "' + cellValue + '"\n')
					});
					
					grid.jqxGrid('refresh');
					
					element.grids[gridName] = grid;
				}
				
				// Load data on select
				$('#attributepanel_grid').on('rowselect', function (event) {
					var args = event.args; 
					var row = args.rowindex;
					var datarow = $("#attributepanel_grid").jqxGrid('getrowdata', row);
					
					for (var i = 0; i < element.gridNames.length; i++) {
						var gridName = element.gridNames[i];
						var grid = element.grids[gridName];
						var adapter = grid.jqxGrid('source');
						element.clearAttrList(gridName)
						if( adapter.getattributescmd == '' )
							continue;
						window['interface'].serverCommand(adapter.getattributescmd + ' ' + datarow['name'] + ' 0\n')
					}
				});
			}
		});
		
		// Use close event to update the visibility state
		this.content.on('close', function (/*event*/) 
		{ 
			element.obj.onSetVisible(false);
		});
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

	// Functions for abilities list
	clearList() {
		this.abilities = [];
		this.source.localdata = this.abilities;
	}

	addAbility(name) {
		this.abilities.push(name);
		this.source.localdata = this.abilities;
	}

	addAbilities(names) {
		this.abilities.push.apply(this.abilities, names)
		this.source.localdata = this.abilities;
	}

	// Functions for grids in tabs
	clearAttrList(tabname) {
		var grid = $(this.content).find("#attributepanel_grid"+tabname);
		var adapter = grid.jqxGrid('source');
		if( adapter === undefined )
			return;
		adapter.contentsource.localdata = [];
		if( adapter.refreshtimeout == null )
			adapter.refreshtimeout = setTimeout(this.refreshAttributeGrid, 100, this, tabname);
	}

	addAttribute(tabname, entry) {
		var grid = $(this.content).find("#attributepanel_grid"+tabname);
		var adapter = grid.jqxGrid('source');
		if( adapter === undefined )
			return;
			
		var localdata = adapter.contentsource.localdata;
		var found = false;
		for( var i = 0; i < localdata.length; i++ )
		{
			if( localdata[i]['attribute'] == entry['attribute'] )
			{
				localdata[i] = entry;
				found = true;
				break;
			}
		}
		
		if( !found )
		{
			adapter.contentsource.localdata.push(entry);
		}
		if( adapter.refreshtimeout == null )
			adapter.refreshtimeout = setTimeout(this.refreshAttributeGrid, 100, this, tabname);
	}

	addAttributes(tabname, entries) {
		for( var i = 0; i < entries.length; i++ )
		{
			this.addAttribute(tabname, entries[i]);
		}
	}

	// Delays refreshing the grid
	refreshAttributeGrid(element, tabname) {
		var grid = $(element.content).find("#attributepanel_grid"+tabname);
		var adapter = grid.jqxGrid('source');
		if( adapter === undefined )
			return;
		adapter.refreshtimeout = null;
		grid.jqxGrid({ source: adapter });
	}
}
