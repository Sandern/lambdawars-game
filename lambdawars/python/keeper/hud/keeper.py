from core.hud import HudInfo
from core.resources import resources
from core.signals import resourceset, refreshhud
from core.abilities import GetAbilityInfo
from gameinterface import engine
from entities import CBasePlayer
from gamerules import gamerules

from cef import CefPanel, viewport


class HudKeeper(CefPanel):
    htmlfile = 'ui/viewport/keeper/keeper.html'
    classidentifier = 'viewport/hud/keeper/Keeper'
    cssfiles = CefPanel.cssfiles + ['keeper/keeper.css']
    
    goldamount = 0
    maxgold = 0
    
    def __init__(self):
        super(HudKeeper, self).__init__(viewport, 'HudKeeper')

        resourceset.connect(self.OnResourceSet)
        refreshhud.connect(self.OnRefreshHud)
        
        spells = [
            'createimp', 
            'possesscreature',
            'lighting',
            'skheal',
            'increasespeed',
            'calltoarms',
            'reveal',
        ]
        
        rooms = [
            'createtreasureroom',
            'createlair',
            'createhatchery',
            'createtraining',
            #'createlibrary',
            #'createworkshop',
            
            'sellroom',
        ]
        
        self.buttons = []
        
        for s in spells:
            info = GetAbilityInfo(s)
            if not info:
                PrintWarning('HudKeeper: invalid spell/room\n')
                continue
            self.AddButton(info, '#swarmkeeper_spells')

        for r in rooms:
            info = GetAbilityInfo(r)
            if not info:
                PrintWarning('HudKeeper: invalid spell/room\n')
                continue
            self.AddButton(info, '#swarmkeeper_rooms')
        
        self.buttoninst = []
        
    def AddButton(self, info, category):
        if info.costs: gold = info.costs[0][0][1]
        else: gold = None
   
        self.buttons.append({
            'name' : info.name, # Name/command
            'displayname' : info.displayname,
            'tooltip' : info.description,
            'category' : category,
            'costs' : gold,
        })
        
    def Remove(self):
        super(HudKeeper, self).Remove()
        
        resourceset.disconnect(self.OnResourceSet)
        refreshhud.disconnect(self.OnRefreshHud)
        
    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = super(HudKeeper, self).GetConfig()
        config['visible'] = True
        return config
        
    def OnLoaded(self):
        super(HudKeeper, self).OnLoaded()
    
        self.visible = True

        self.CreateFunction('onCommand', False)

        for b in self.buttons:
            setattr(self, 'button%s' % (b['name'].lower()), 
                self.InvokeWithResult("insertItem", [b]))

        player = CBasePlayer.GetLocalPlayer()
        if player and hasattr(player, 'maxgold'): 
            self.maxgold = player.maxgold 
            self.SetGold(resources[player.GetOwnerNumber()]['gold'])
    
    def OnResourceSet(self, ownernumber, type, amount, **kwargs):
        if type == 'gold':
            self.SetGold(amount)
            
    def OnRefreshHud(self, **kwargs):
        player = CBasePlayer.GetLocalPlayer()
        if not player:
            return
        if hasattr(player, 'maxgold'):
            self.maxgold = player.maxgold
        self.RefreshGoldHud()
        
        if hasattr(self, 'buttoncreateimp'):
            self.viewport.Invoke(self.buttoncreateimp, 'html', ['%s (%s)' % ('Create Imp', 
                    gamerules.GetCreateImpCost(player.GetOwnerNumber()))])
        
    def SetGold(self, goldamount):
        self.goldamount = goldamount
        self.RefreshGoldHud()
        
    def RefreshGoldHud(self):
        self.Invoke("setGold", [str(self.goldamount), str(self.maxgold)])
        
    def DoAbility(self, abiname):
        engine.ServerCommand('player_ability %s' % (abiname))
        
    def onCommand(self, methodargs, callbackid):
        command = methodargs[0]
        self.DoAbility(command)

class HudKeepersettings(CefPanel):
    htmlfile = 'ui/viewport/keeper/settings.html'
    classidentifier = 'viewport/hud/keeper/Settings'
    cssfiles = CefPanel.cssfiles + ['keeper/keeper.css']
    
    def __init__(self):
        super(HudKeepersettings, self).__init__(viewport, 'HudKeeperSettings')

    def OnLoaded(self):
        super(HudKeepersettings, self).OnLoaded()
        
        self.visible = True
        
class KeeperHudInfo(HudInfo):
    name = 'keeper_hud'
    cefcls = [HudKeeper, HudKeepersettings]
