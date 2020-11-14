from entities import CBasePlayer
from core.usermessages import usermessage
from cef import viewport, CefPanel
from gameinterface import engine
from core.factions import GetFactionInfo
from core.signals import playerchangedfaction

class HudOverrun(CefPanel):
    name = 'overrun'
    
    @property
    def htmlfile(self):
        htmlfile = 'ui/viewport/wars/overrun_rebels.html'
        player = CBasePlayer.GetLocalPlayer()
        if not player:
            return htmlfile
            
        faction = player.GetFaction()
        factioninfo = GetFactionInfo(faction)
        if not factioninfo:
            return htmlfile
            
        return getattr(factioninfo, 'overrunhud_htmlfile', htmlfile)
            
    classidentifier = 'viewport/hud/wars/Overrun'
    cssfiles = CefPanel.cssfiles + ['wars/overrun.css']
    
    wave = 0
    nextwavetime = 0.0
    waveprogress = 0.0
    
    def __init__(self, *args, **kwargs):
        super(HudOverrun, self).__init__(*args, **kwargs)
    
        # Register UpdateWaveInfo as usermessage
        self.UpdateWaveInfo = usermessage('overrun.waveupdate')(self.UpdateWaveInfo)
        self.UpdateWaveProgress = usermessage('overrun.waveprogress')(self.UpdateWaveProgress)
        
        playerchangedfaction.connect(self.OnPlayerFactionChanged)
        
    def SetupFunctions(self):
        super(HudOverrun, self).SetupFunctions()
        
        self.CreateFunction('onReady', False)
        
    def OnLoaded(self):
        super(HudOverrun, self).OnLoaded()
        
        self.visible = True
        self.UpdateWaveInfo(self.wave, self.nextwavetime)
        self.UpdateWaveProgress(self.waveprogress)
        
    def Remove(self):
        super(HudOverrun, self).Remove()
        
        playerchangedfaction.disconnect(self.OnPlayerFactionChanged)
        
    def OnPlayerFactionChanged(self, player, oldfaction, **kwargs):
        self.LoadCode()
        self.ReplaceContent(self.htmlcode)
        
    def UpdateWaveInfo(self, wave, nextwavetime, **kwargs):
        ''' Updates wave information. 
        
            Args:
                wave(int): The current wave number
                nextwavetime (float): time in future at which the next wave occurs. 
                                      If this time is in the past, the current wave is progress.
        '''
        self.wave = wave
        self.nextwavetime = nextwavetime
        
        if self.isloaded:
            wavecountdown = int(self.nextwavetime - gpGlobals.curtime)
            self.Invoke("setNextWaveCountdown", [wave, wavecountdown])
            
    def UpdateWaveProgress(self, progress, **kwargs):
        ''' Update of wave progress about once per second if progress changes. 
        
            Args:
                progress(float): Progress ranging from 0.0 to 1.0.
        ''' 
        self.waveprogress = progress
        
        if self.isloaded:
            self.Invoke("updateWaveProgress", [self.waveprogress])
        
    def onReady(self, methodargs, callbackid):
        ''' Callback for when the player presses the ready button for next wave. '''
        engine.ServerCommand('overrun_wave_ready')

