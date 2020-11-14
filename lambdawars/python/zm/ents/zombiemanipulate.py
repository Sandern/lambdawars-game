from srcbase import *
from vmath import *
from entities import entity, IMouse
from gamerules import GameRules
if isserver:
    from entities import CBaseAnimating as BaseAnimating, gEntList, CreateEntityByName, DispatchSpawn, CBaseTrigger
    from utils import UTIL_PrecacheOther, UTIL_ClientPrintAll, HUD_PRINTTALK, UTIL_Remove, ClientPrint, UTIL_SetSize
    from gameinterface import CSingleUserRecipientFilter
else:
    from entities import C_BaseAnimating as BaseAnimating, C_BasePlayer

from zm.shared import *
from zm.gamerules.zm import ZMResources
from fields import IntegerField, StringField, BooleanField, input, OutputField
from ..hud import ShowManipulateMenu

@entity('info_manipulate', networked=True)
class ZombieManipulate(BaseAnimating, IMouse):
    def __init__(self):
        BaseAnimating.__init__(self)
        IMouse.__init__(self) 
        
    def GetIMouse(self):
        return self
        
    description = StringField(value='', keyname='Description', networked=True)
    cost = IntegerField(value=0, keyname='Cost', networked=True)
    trapcost = IntegerField(value=0, keyname='TrapCost', networked=True)
    active = BooleanField(value=False, keyname='Active')
        
    if isserver:
        removeontrigger = BooleanField(value=False, keyname='RemoveOnTrigger')
        onpressed = OutputField(keyname='OnPressed')
        
        nextchangetime = 0.0
        trapcount = 0
        parentmanipulate = None
        
        def OnClickLeftPressed(self, player):
            if not self.active:
                return
            player.lastselected = self.entindex()

            filter = CSingleUserRecipientFilter(player) # set recipient
            filter.MakeReliable()  # reliable transmission
            ShowManipulateMenu(self, filter=filter)
                
        def Precache(self):
            self.PrecacheModel(MANIPULATE_MODEL)

            UTIL_PrecacheOther("info_manipulate_trigger")
            
        def Spawn(self):
            self.Precache()

            self.SetModel(MANIPULATE_MODEL)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_TRIGGER|FSOLID_NOT_SOLID)
            self.SetSolid(SOLID_BBOX)
            UTIL_SetSize( self, -Vector(20,20,20), Vector(20,20,20) )
            self.SetMoveType(MOVETYPE_FLY)
            
            if not self.active:
                self.AddEffects(EF_NODRAW)
            else:
                self.RemoveEffects(EF_NODRAW)
          
        @input(inputname='Toggle')
        def InputToggle(self, inputData):
            # Toggle our active state
            if self.active:
                self.active = False
                self.AddEffects(EF_NODRAW)
            else:
                self.active = True
                self.RemoveEffects(EF_NODRAW)
            
            #LAWYER:  Destroy all Traps linked to self object
            for pSelector in zombietraps:
                if pSelector:
                    #Cycle through all of the Traps
                    if pSelector.parentmanipulate == self:
                        UTIL_Remove(pSelector) #Pop them if they're parented
                        
        @input(inputname='Hide')
        def InputHide(self, inputData):
            # hide self!
            self.active = False
            self.AddEffects(EF_NODRAW)

            #LAWYER:  Destroy all Traps linked to self object
            for pSelector in zombietraps:
                if pSelector:
                    #Cycle through all of the Traps
                    if pSelector.parentmanipulate == self:
                        UTIL_Remove(pSelector) #Pop them if they're parented
        
        @input(inputname='Unhide')
        def InputUnhide(self, inputData):
            # unhide self!
            self.active = True
            self.RemoveEffects(EF_NODRAW)

        def Trigger(self, pActivator):
            #TGB: we don't want to be able to activate hidden manips
            if self.active == False:
                return

            # Msg("Pressed...\n") #LAWYER
            self.onpressed.FireOutput(pActivator, self)  #Fire outputs when triggered.

            #LAWYER:  Destroy all Traps linked to self object
            for pSelector in zombietraps:
                if pSelector:
                    #Cycle through all of the Traps
                    if pSelector.parentmanipulate == self:
                        UTIL_Remove(pSelector) #Pop them if they're parented

            #TGB: zero the trap count seeing as we just removed them all
            self.trapcount = 0

            GameRules().ManipulateTriggered(self)

            if self.removeontrigger == True:
                #LAWYER:  Remove self entity!
                UTIL_Remove(self)
    else:
        def ShouldDraw(self):
            player = C_BasePlayer.GetLocalPlayer()
            if not player or ZMResources().zmplayer != player:
                return False
            return super(ZombieManipulate, self).ShouldDraw()
            
        def Spawn(self):
            super(ZombieManipulate, self).Spawn()
            
            zombiemastervisible.append(self.GetHandle())
            
        def UpdateOnRemove(self):
            super(ZombieManipulate, self).UpdateOnRemove()
            
            try: zombiemastervisible.remove(self.GetHandle())
            except ValueError: pass # Already removed
        
@entity('info_manipulate_trigger', networked=True)
class ZombieManipulateTrigger(BaseAnimating):
    def Precache(self):
        self.PrecacheModel(TRAP_MODEL)

    def Spawn(self):
        if isserver:
            self.Precache()

            self.SetModel( TRAP_MODEL )
            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_TRIGGER|FSOLID_NOT_SOLID)
            self.SetSolid(SOLID_BBOX)
            UTIL_SetSize( self, -Vector(20,20,20), Vector(20,20,20) )
            self.SetMoveType(MOVETYPE_FLY)
            self.RemoveEffects(EF_NODRAW)

            self.SetThink(self.ScanThink)
            self.SetNextThink( gpGlobals.curtime + 0.5)
        
        zombiemastervisible.append(self.GetHandle())
        
    def UpdateOnRemove(self):
        super(ZombieManipulateTrigger, self).UpdateOnRemove()

        try: zombiemastervisible.remove(self.GetHandle())
        except ValueError: pass # Already removed
    
    def Trigger(self):
    #	Msg("Pressed...\n") #LAWYER
    #	m_OnPressed.FireOutput(pActivator, self)  #Fire outputs when triggered.
    #	if (m_bRemoveOnTrigger == True)
    #	
        if self.parentmanipulate and self.parentmanipulate.active:
            self.parentmanipulate.Trigger(self) #Can only trigger when the original thing is fired!
            self.parentmanipulate.RemovedTrap() #adjust trap count on manip

        UTIL_Remove( self ) #LAWYER:  kill Traps when they've been triggered

    def ScanThink(self):
        #LAWYER:  We need to do a scan thing
        pIterated = gEntList.FindEntityInSphere(None, self.GetAbsOrigin(), zm_trap_triggerrange.GetInt())
        while pIterated: #Should probably be a smaller search area.  Large games could be squidged by self function
            #pPlayer = dynamic_cast< CBasePlayer * >(pIterated)
            pPlayer = pIterated
            if pPlayer and pPlayer.IsPlayer():
                if pPlayer.GetOwnerNumber() == ON_SURVIVOR:
                    self.Trigger()
                    return #TGB: no use looping on if we already triggered
            pIterated = gEntList.FindEntityInSphere(pIterated, self.GetAbsOrigin(), zm_trap_triggerrange.GetInt())
            
        self.SetNextThink( gpGlobals.curtime + 0.5 )
        
    def ShouldDraw(self):
        player = C_BasePlayer.GetLocalPlayer()
        if not player or ZMResources().zmplayer != player:
            return False
        return super(ZombieManipulateTrigger, self).ShouldDraw()
        
        