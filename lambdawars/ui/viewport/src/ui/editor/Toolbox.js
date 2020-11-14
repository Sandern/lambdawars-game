import { ViewportElement } from '../../viewport/ViewportElement';

import { CoverPanel } from './CoverPanel';
import { NavMeshPanel } from './NavMeshPanel';
import { PropertiesPanel } from './PropertiesPanel';

export class Toolbox extends ViewportElement {
		constructor(name, config) {
			super(name, config);
			
			// summary:
			//            Constructs wars editor toolbox panel
			this.activemode = 'select';
			
			this.propertiesPanel = null;
			this.navmeshPanel = null;
			this.coverPanel = null;
			this.numselected = 0;
		}

		initContent() {
			this.initToolbox();
			this.initFloraPanel();
		}

		setVisible(state) {
			if( this.content.is(":visible") == state )
				return;
				
			if( !state ) {
				this.content.show();
			}
			else {
				this.content.hide();
				this.floraPanel.jqxWindow('close');
			}
		}

		onRemove() {
			// summary:
			//            Cleans up the toolbox and panels.
			$('div').remove('#editor_florapanel');
			if( this.propertiesPanel ) {
				this.propertiesPanel.destroyPanel();
			}
			if( this.navmeshPanel ) {
				this.navmeshPanel.destroyPanel();
			}
			if( this.coverPanel ) {
				this.coverPanel.destroyPanel();
			}
		}

		initToolbox() {
			// summary:
			//            Setup the toolbox
			
			// Add Select, transform and rotate
			var element = this;
			var SelectedElement = "";
			var SelectedElementID = this.content.find('#editor_toolbox_select');
			this.content.find('#editor_toolbox_select').click(function() {
				SelectedElementID.attr('src','images/flora_editor/box_bg.png');
				SelectedElementID = $(this);
				SelectedElement = $(this).attr( 'titel' );
				$(this).attr('src','images/flora_editor/box_bg_select.png');
				
				element.setActiveMode('select');
				element.content.find('#editor_toolbox_select').blur();
			});
			this.content.find('#editor_toolbox_transform').click(function() {
				SelectedElementID.attr('src','images/flora_editor/box_bg.png');
				SelectedElementID = $(this);
				SelectedElement = $(this).attr( 'titel' );
				$(this).attr('src','images/flora_editor/box_bg_select.png');
				
				element.setActiveMode('translate');
				element.content.find('#editor_toolbox_transform').blur();
			});
			this.content.find('#editor_toolbox_rotate').click(function() {
				SelectedElementID.attr('src','images/flora_editor/box_bg.png');
				SelectedElementID = $(this);
				SelectedElement = $(this).attr( 'titel' );
				$(this).attr('src','images/flora_editor/box_bg_select.png');
				
				element.setActiveMode('rotate');
				element.content.find('#editor_toolbox_rotate').blur();
			});
			
			// Tools
			this.content.find('#editor_toolbox_flora').click(function() {
				//$(this).attr('src','images/flora_editor/box_bg_press.png');
				
				element.setActiveMode('flora');
				window['interface'].serverCommand('wars_abi editor_tool_flora');
				element.content.find('#editor_toolbox_flora').blur();
			});
			
			this.content.find('#editor_toolbox_navmesh').click(function() {
				element.setActiveMode('navmesh');
				//window['interface'].serverCommand('wars_abi editor_tool_navmesh');
				element.content.find('#editor_toolbox_navmesh').blur();
			});
			
			this.content.find('#editor_toolbox_cover').click(function() {
				element.setActiveMode('cover');
				window['interface'].serverCommand('wars_abi editor_tool_cover');
				element.content.find('#editor_toolbox_cover').blur();
			});
			
			element.content.find('#editor_toolbox_properties').click(function() {
				if( element.propertiesPanel === null ) {
					element.propertiesPanel = new PropertiesPanel(element, element.content, '#editor_propertiespanel', this.numselected);
				}
				
				if( element.propertiesPanel.propertiesPanel.is(":visible") ) {
					element.propertiesPanel.propertiesPanel.jqxWindow('close');
				} else {
					element.propertiesPanel.propertiesPanel.jqxWindow('open');
				}
				
				element.content.find('#editor_toolbox_properties').blur();
			});
			
			element.content.find('#editor_toolbox_navmesh').click(function() {
				if( element.navmeshPanel === null ) {
					element.navmeshPanel = new NavMeshPanel(element, element.content, '#editor_navmeshpanel', this.numselected);
				}
				
				if( element.navmeshPanel.navmeshPanel.is(":visible") ) {
					element.navmeshPanel.navmeshPanel.jqxWindow('close');
				} else {
					element.navmeshPanel.navmeshPanel.jqxWindow('open');
				}
				
				element.content.find('#editor_toolbox_navmesh').blur();
			});
			
			element.content.find('#editor_toolbox_cover').click(function() {
				if( element.coverPanel === null ) {
					element.coverPanel = new CoverPanel(element, element.content, '#editor_coverpanel');
				}
				
				if( element.coverPanel.coverPanel.is(":visible") ) {
					element.coverPanel.coverPanel.jqxWindow('close');
				} else {
					element.coverPanel.coverPanel.jqxWindow('open');
				}
				
				element.content.find('#editor_toolbox_cover').blur();
			});
			
			// Saving
			this.content.find('#editor_toolbox_savemap').click(function() {
				//$(this).attr('src','images/flora_editor/box_bg_press.png');
				
				window['interface'].serverCommand('wars_editor_save');
				element.content.find('#editor_toolbox_savemap').blur();
			});
			
			const theme = 'wars';
			//ToolTip
			this.content.find( "#editor_toolbox div img:nth-child(1)").each(function() {
				$(this).jqxTooltip({
					content: $(this).attr( 'titel' ),
					position: 'right',
					name: 'Tooltip',
					showArrow: true,
					theme: theme
				});
			});
				
			//Roll Over
			this.content.find( "#editor_toolbox div img:nth-child(1)").mouseover(function() {
				if ( $(this).attr( 'titel' ) != SelectedElement)
					$(this).attr('src','images/flora_editor/box_bg_over.png');
				return false;
			});

			//Roll Out
			this.content.find( "#editor_toolbox div img:nth-child(1)").mouseout(function() {
				if ( $(this).attr( 'titel' ) != SelectedElement)
					$(this).attr('src','images/flora_editor/box_bg.png');
				return false;
			});
			
		}

		getTextElementByColor(color) {
			// summary:
			//            Helper for color picker
			if (color == 'transparent' || color.hex == "") {
				return $("<div style='text-shadow: none; position: relative; padding-bottom: 2px; margin-top: 2px;'>transparent</div>");
			}
			var element = $("<div style='text-shadow: none; position: relative; padding-bottom: 2px; margin-top: 2px;'>#" + color.hex + "</div>");
			var nThreshold = 105;
			var bgDelta = (color.r * 0.299) + (color.g * 0.587) + (color.b * 0.114);
			var foreColor = (255 - bgDelta < nThreshold) ? 'Black' : 'White';
			element.css('color', foreColor);
			element.css('background', "#" + color.hex);
			element.addClass('jqx-rc-all');
			return element;
		}

		initFloraPanel() {
			// summary:
			//            Setup the Flora panel
			var element = this;

			var theme = 'wars';
			var floraPanel = element.content.find('#editor_florapanel');
			this.floraPanel = floraPanel;
			
			floraPanel.jqxWindow({
				showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 200, maxWidth: 2000, maxHeight: 2000, height: 400, width: 450, theme: theme, autoOpen: false,
				initContent: function () {
					// create Tree Grid
					var floratreegrid = floraPanel.find('#editor_treegrid');
					$(floratreegrid).jqxTreeGrid(
					{
						width: '97%',
						theme: theme,
						selectionMode: 'multipleRows',
						//columnsHeight: 25,
						filterable: true,
						ready: function () {
							floratreegrid.jqxTreeGrid('expandRow', '2');
						},
						columns: [
							{ text: 'Model', dataField: 'Model', width: '100%', cellClassName : 'editor_treegrid_cell', filtertype: 'textbox', filtercondition: 'contains' },
						],
						// Dynamically load data per node
						virtualModeCreateRecords: function(expandedRecord, done)
						{
							element.obj.listModels(expandedRecord ? expandedRecord['FullPath'] : 'models/', function(records) {
								// prepare the data
								var source =
								{
									dataType: "array",
									dataFields: [
										{ name: "Model", type: "string" },
										{ name: "FullPath", type: "string" },
										{ name: "ModelID", type: "string" },
									],
									localData:  records,
									id: 'ModelID',
								}
								var dataAdapter = new $.jqx.dataAdapter(source, {
									loadComplete: function () {
										done(dataAdapter.records);
									}
								});
								dataAdapter.dataBind();
							});
						},
						virtualModeRecordCreating: function(record)
						{
							var ext = record['Model'].split('.').pop();
							if (ext == 'mdl') {
								// by setting the record's leaf member to true, you will define the record as a leaf node.
								record.leaf = true;
							}
						},
					});
					
					// Create density slider
					var floradensityslider = floraPanel.find('#editor_density_slider');
					floradensityslider.jqxSlider({
						width:"100%",
						theme: theme,
						min: 0.0,
						max: 5.0,
						value: 1.0,
					});
					
					floradensityslider.on('change', function (event) {
						var value = event.args.value;
						element.obj.setPlaceToolDensity(value);
					});
					
					// Create Place on Nav Mesh checkbox
					var floranavmeshcheckbox = floraPanel.find('#editor_navmesh_checkbox');
					floranavmeshcheckbox.jqxCheckBox({ width: 120, height: 25, checked:true, theme:theme });

					floranavmeshcheckbox.bind('change', function (event) {
						var checked = event.args.checked;
						element.obj.setPlaceToolPlaceOnNavMesh(checked);
					});
					
					// Create Ignore Clips checkbox
					var floraignoreclipscheckbox = floraPanel.find('#editor_ignoreclips_checkbox');
					floraignoreclipscheckbox.jqxCheckBox({ width: 120, height: 25, checked:false, theme:theme });

					floraignoreclipscheckbox.bind('change', function (event) {
						var checked = event.args.checked;
						element.obj.setPlaceToolAttribute('ignoreclips', checked);
					});
					
					// Color picker
					var floracolorpickerdropdown = floraPanel.find('#editor_colorpicker_dropdown');
					var floracolorpicker = floraPanel.find('#editor_colorpicker');
					floracolorpicker.on('colorchange', function (event) {
						floracolorpickerdropdown.jqxDropDownButton('setContent', element.getTextElementByColor(event.args.color));
						element.obj.setPlaceToolAttribute('color', event.args.color.r + ' ' + event.args.color.g + ' ' + event.args.color.b);
					});
					floracolorpicker.jqxColorPicker({ color: "ffffff", colorMode: 'hue', width: 150, height: 150, theme:theme});
					floracolorpickerdropdown.jqxDropDownButton({ width: 150, height: 22, theme:theme});
					floracolorpickerdropdown.jqxDropDownButton('setContent', element.getTextElementByColor(new $.jqx.color({ hex: "ffffff" })));
						
					// Bind events
					floratreegrid.on('rowSelect', function (/*event*/) {
						// Get row data
						// rowSelect event is bugged with shift select. Just always select everything again.
						var selection = floratreegrid.jqxTreeGrid('getSelection');
						for (var i = 0; i < selection.length; i++) {
							// get a selected row.
							var rowData = selection[i];
							element.obj.addPlaceToolAsset(rowData['FullPath']);
						}
					});
					floratreegrid.on('rowUnselect ', function (event) {
						// Get row data
						var args = event.args;
						var row = args.row;
						//var key = args.key;
						
						element.obj.removePlaceToolAsset(row['FullPath']);
					});
				}
			});
		}

		initNavMeshPanel() {
			
		}

		editorSelectionChanged(numselected) {
			this.numselected = numselected;
			if( this.propertiesPanel ) {
				this.propertiesPanel.updateTitle(numselected);
				if( this.propertiesPanel.propertiesPanel.is(":visible") ) {
					this.propertiesPanel.refreshProperties(numselected);
				}
			}
		}

		setActiveMode(mode) {
			// summary:
			//            Changes the active mode
			if( mode === 'flora' ) {
				this.floraPanel.jqxWindow('open');
				// TODO: Maybe instead of clearing the selection, reapply the selection?
				this.floraPanel.find('#editor_treegrid').jqxTreeGrid('clearSelection');
			}
			else if( mode === 'navmesh' ) {
				this.floraPanel.jqxWindow('close');
			}
			else {
				this.floraPanel.jqxWindow('close');
			}
			
			this.activemode = mode;
			this.obj.setActiveMode(mode);
		}
}
