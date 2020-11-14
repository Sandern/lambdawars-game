from cef import WebViewComponent, jsbind
from gameinterface import engine
import filesystem

from datetime import datetime

class WebSavedGames(WebViewComponent):
    defaultobjectname = 'savedgames'
    
    @jsbind(hascallback=True)
    def getSavedGames(self, methodargs):
        ''' Returns list of saved games. '''
        return [filesystem.ListDir(path="save/", wildcard="*.sav")]
        
    @jsbind()
    def loadSavedGame(self, methodargs):
        ''' Loads given saved game. '''
        engine.ClientCommand('maxplayers 1')
        engine.ClientCommand('load "%s"' % methodargs[0])
        
    @jsbind()
    def saveGame(self, methodargs):
        ''' Saves game. '''
        print('Args save: %s' % (str(methodargs)))
        engine.ClientCommand('save "%s"' % (methodargs[0] if len(methodargs) > 0 and methodargs[0] else 'Saved Game %s' % datetime.now().strftime("%d-%m-%y %H-%M-%S")))
