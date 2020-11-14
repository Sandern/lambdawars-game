export class NavMeshPanel {
	constructor(element, content, panelId/*, numselected*/) {
		// summary:
		//            
		var self = this;
		this.element = element;
		this.panelId = panelId;
		this.content = content;
		this.navmeshPanel = this.content.find(panelId);
		var navmeshPanel = this.navmeshPanel;
		
		var theme = 'wars';
		navmeshPanel.jqxWindow({
			showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 150, maxWidth: 2000, maxHeight: 2000, height: 400, width: 200, theme: theme, autoOpen: false,
			initContent: function () {
				// Build nav mesh
				navmeshPanel.find('#editor_navmesh_build').jqxButton({ width: '100px', height: '20px', theme: theme});
				navmeshPanel.find('#editor_navmesh_build').bind('click', function () {
					window['interface'].serverCommand('recast_build\n');
				});
				
				// Drop down to select mesh for visualization
				var source = [
					{ label : 'human', value : 'human' },
					{ label : 'medium', value : 'medium' },
					{ label : 'large', value : 'large' },
					{ label : 'verylarge', value : 'verylarge' },
					{ label : 'air', value : 'air' },
				];
				navmeshPanel.find('#editor_navmesh_dropdown').jqxDropDownList({ source: source, width: '100px', height: '25px', selectedIndex: 1, enableBrowserBoundsDetection: true, theme: theme});
				navmeshPanel.bind('change', function (event) { 
					var args = event.args;
					if (args) {               
						var item = args.item;
						var value = item.value;
						window['interface'].clientCommand('recast_debug_mesh ' + value + '\n');
						self.updateMeshSettings(value, false);
					}
				});
				
				// Draw nav mesh checkbox
				var drawnavmeshcheckbox = navmeshPanel.find('#editor_navmesh_draw_checkbox');
				drawnavmeshcheckbox.jqxCheckBox({ width: 120, height: 25, checked:false, theme:theme });

				drawnavmeshcheckbox.bind('change', function (event) {
					var checked = event.args.checked;
					window['interface'].clientCommand('recast_draw_navmesh ' + (checked ? '1' : '0'));
				});
				
				// Toggle server/client visualization
				var servernavmeshcheckbox = navmeshPanel.find('#editor_navmesh_server_checkbox');
				servernavmeshcheckbox.jqxCheckBox({ width: 120, height: 25, checked:false, theme:theme });

				servernavmeshcheckbox.bind('change', function (event) {
					var checked = event.args.checked;
					window['interface'].clientCommand('recast_draw_server ' + (checked ? '1' : '0'));
				});
				
				// Settings
				function getDebugMesh() {
					return navmeshPanel.find('#editor_navmesh_dropdown').jqxDropDownList('val');
				}
				navmeshPanel.find("#editor_navmesh_cellsize").jqxInput({ width: 50, height: 25 });
				navmeshPanel.find("#editor_navmesh_cellsize").on('change', function () {
					var value = navmeshPanel.find('#editor_navmesh_cellsize').val();
					element.obj.meshSetCellSize(getDebugMesh(), value);
				});
				
				navmeshPanel.find("#editor_navmesh_cellheight").jqxInput({ width: 50, height: 25 });
				navmeshPanel.find("#editor_navmesh_cellheight").on('change', function () {
					var value = navmeshPanel.find('#editor_navmesh_cellheight').val();
					element.obj.meshSetCellHeight(getDebugMesh(), value);
				});
				
				navmeshPanel.find("#editor_navmesh_tilesize").jqxInput({ width: 50, height: 25 });
				navmeshPanel.find("#editor_navmesh_tilesize").on('change', function () {
					var value = navmeshPanel.find('#editor_navmesh_tilesize').val();
					element.obj.meshSetTileSize(getDebugMesh(), value);
				});
			}
		});
		
		navmeshPanel.on('open', function () {
			self.updateMeshSettings('', true);
		}); 
	}

	destroyPanel() {
		$('div').remove(this.panelId);
	}
	
	updateMeshSettings(meshName, updateDropDown) {
		var navmeshPanel = this.navmeshPanel;
		this.element.obj.getMeshSettings(meshName, function(settings) {
			if( updateDropDown === true ) {
				navmeshPanel.find('#editor_navmesh_dropdown').jqxDropDownList('val', settings.debug_mesh);
			}
			navmeshPanel.find('#editor_navmesh_draw_checkbox').jqxCheckBox('val', settings.draw_navmesh);
			navmeshPanel.find('#editor_navmesh_server_checkbox').jqxCheckBox('val', settings.draw_server);
			navmeshPanel.find("#editor_navmesh_cellsize").jqxInput('val', settings.cellsize);
			navmeshPanel.find("#editor_navmesh_cellheight").jqxInput('val', settings.cellheight);
			navmeshPanel.find("#editor_navmesh_tilesize").jqxInput('val', settings.tilesize);
		});
	}
}
