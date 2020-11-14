export class CoverPanel {
	constructor(element, content, panelId) {
		// summary:
		//            
		this.element = element;
		this.panelId = panelId;
		this.content = content;
		this.coverPanel = this.content.find(panelId);
		var coverPanel = this.coverPanel;
		
		var theme = 'wars';
		coverPanel.jqxWindow({
			showCollapseButton: true, keyboardCloseKey: 'none', minHeight: 200, minWidth: 150, maxWidth: 2000, maxHeight: 2000, height: 400, width: 200, theme: theme, autoOpen: false,
			initContent: function () {
				// Build nav mesh
				coverPanel.find('#editor_cover_convertnavmesh').jqxButton({ width: '100px', height: '20px', theme: theme});
				coverPanel.find('#editor_cover_convertnavmesh').bind('click', function () {
					window['interface'].serverCommand('cover_convert_oldnavmesh\n');
				});
			}
		});
		
		coverPanel.on('open', function () {
			
		}); 
	}

	destroyPanel() {
		$('div').remove(this.panelId);
	}
} 
