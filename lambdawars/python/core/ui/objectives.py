from cef import viewport, CefPanel
from core.signals import prelevelinit

class CefObjectivesPanel(CefPanel):
    htmlfile = 'ui/viewport/wars/objectives.html'
    classidentifier = 'viewport/hud/wars/Objectives'
    cssfiles = CefPanel.cssfiles + ['wars/objectives.css']
    
    # The last builded sorted list of objective information for the hud
    objectiveinfo = []
    # The last received list of valid objective entities
    objectiveents = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        prelevelinit.connect(self.OnPreLevelInit)
        
    def OnLoaded(self):
        super().OnLoaded()
        
        self.RebuildObjectiveList(self.objectiveents)
        
    def OnRemove(self):
        super().OnRemove()
        
        prelevelinit.disconnect(self.OnPreLevelInit)
        
    def OnPreLevelInit(self, **kwargs):
        ''' Resets the objective list on level init. '''
        self.objectiveinfo = []
        if self.isloaded:
            self.UpdateObjectiveList()
        
    def RebuildObjectiveList(self, objectiveents):
        ''' Rebuilds the objective list from scratch from the passed objective entities list. '''
        self.objectiveents = objectiveents
        
        # Build info list
        self.objectiveinfo = []
        for ent in objectiveents:
            if not ent or not ent.visible:
                continue
                
            self.objectiveinfo.append(ent.BuildObjectInfo())
            
        # Sort on priority...
        self.objectiveinfo = sorted(self.objectiveinfo, key=lambda v: v['priority'], reverse=True)
        
        # Do the update
        self.UpdateObjectiveList()
        
    def UpdateObjectiveList(self):
        ''' Calls the javascript part to rebuild the html list of objectives. '''
        # Got anything to display?
        if not self.objectiveinfo:
            self.visible = False
            return
            
        self.visible = True
        
        self.Invoke("rebuildObjectiveList", [self.objectiveinfo])
        
objectivespanel = CefObjectivesPanel(viewport, 'objectivespanel')
