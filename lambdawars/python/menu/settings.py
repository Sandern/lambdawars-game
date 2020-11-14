from cef import WebViewComponent, jsbind
from gameui import CGameUIConVarRef

class WebSettings(WebViewComponent):
    settings = [
    ]
    
    def BuildCurrentSettings(self):
        settings = copy.deepcopy(self.settings)
        for setting in settings:
            settingconvar = CGameUIConVarRef(setting['name'])
            setting['value'] = settingconvar.GetString()
            if setting['displayname'][0] == '#':
                setting['displayname'] = localize.Find(setting['displayname'])
            if 'choices' in setting:
                for choice in setting['choices']:
                    if choice[1][0] == '#':
                        choice[1] = localize.Find(choice[1])
                
        return settings
    
    def BuildRecommendedSettings(self):
        pass
        
    @jsbind(hascallback=True)
    def getCurrentSettings(self, methodargs):
        return [self.BuildCurrentSettings()]
        
    @jsbind()
    def apply(self, methodargs):
        ''' Applies settings to game. '''
        pass
        
class WebVideoSettings(WebSettings):
    defaultobjectname = 'videosettings'
    
    settings = [
        {
            'name' : 'gpu_mem_level', 
            'displayname' : '#L4D360UI_VideoOptions_Model_Texture_Detail',
            'choices' : [[0, '#GameUI_Low'], [1, '#GameUI_Medium'], [2, '#GameUI_High']],
            'type' : 'dropdown',
        },
        {
            'name' : 'mem_level',
            'displayname' : '#L4D360UI_VideoOptions_Paged_Pool_Mem',
            'choices' : [[0, '#GameUI_Low'], [1, '#GameUI_Medium'], [2, '#GameUI_High']],
            'type' : 'dropdown',
        },
    ]