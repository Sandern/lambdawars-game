export class PropertiesPanel {
	constructor(element, content, propertiesPanelId, numselected) {
		// summary:
		//            
		var self = this;
		this.element = element;
		this.propertiesPanelId = propertiesPanelId;
		this.content = content;
		this.propertiesPanel = this.content.find(propertiesPanelId);
		var propertiesPanel = this.propertiesPanel;
		
		var theme = 'wars';
		propertiesPanel.jqxWindow({
			showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 200, maxWidth: 2000, maxHeight: 2000, height: 400, width: 450, theme: theme, autoOpen: false,
			initContent: function () {
				self.updateTitle(numselected);
				var grid = propertiesPanel.find('#editor_propertiespanel_grid');
			
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
					const args = event.args;
					const cellValue = args.value;
					const oldValue = args.oldvalue;
					// const gridOwner = event.args.owner;
					
					if( cellValue == oldValue )
						return;
					
					const abirowindex = grid.jqxGrid('getselectedrowindex');
					const datarow = grid.jqxGrid('getrowdata', abirowindex);
					
					element.obj.applyProperties([[datarow['attribute'], cellValue]]);
				});
				
				grid.jqxGrid('refresh');
			}
		});
		
		propertiesPanel.on('open', function () {
			self.refreshProperties();
		}); 
	}

	destroyPanel() {
		$('div').remove(this.propertiesPanelId);
	}

	updateTitle(numselected) {
		this.numselected = numselected;
		this.propertiesPanel.jqxWindow({ title: 'Properties' + (numselected ? ' (' + numselected + ' Selected)' : '') });
	}

	refreshProperties() {
		var self = this;
		this.element.obj.getProperties(function(entries) {
			console.log(entries);
			self.addAttributes(entries);
		});
	}

	// Functions for grids in tabs
	clearAttrList() {
		var grid = this.propertiesPanel.find("#editor_propertiespanel_grid");
		var adapter = grid.jqxGrid('source');
		if( adapter === undefined )
			return;
		adapter.contentsource.localdata = [];
		if( adapter.refreshtimeout == null )
			adapter.refreshtimeout = setTimeout(this.refreshAttributeGrid, 100, this);
	}

	addAttribute(entry) {
		var grid = this.propertiesPanel.find("#editor_propertiespanel_grid");
		var adapter = grid.jqxGrid('source');
		if( adapter === undefined ) {
			console.error('PropertiesPanel.addAttribute: no adapter for grid!');
			return;
		}
			
		var localdata = adapter.contentsource.localdata;
		var found = false;
		for( var i = 0; i < localdata.length; i++ ) {
			if( localdata[i]['attribute'] == entry['attribute'] )
			{
				localdata[i] = entry;
				found = true;
				break;
			}
		}
		
		if( !found ) {
			adapter.contentsource.localdata.push(entry);
		}
		
		if( adapter.refreshtimeout == null )
			adapter.refreshtimeout = setTimeout(this.refreshAttributeGrid, 100, this);
	}

	addAttributes(entries) {
		for(var key in entries) {
			this.addAttribute(entries[key]);
		}
	}

	// Delays refreshing the grid
	refreshAttributeGrid(element) {
		var grid = $(element.propertiesPanel).find("#editor_propertiespanel_grid");
		var adapter = grid.jqxGrid('source');
		if( adapter === undefined )
			return;
		adapter.refreshtimeout = null;
		grid.jqxGrid({ source: adapter });
	}
}
