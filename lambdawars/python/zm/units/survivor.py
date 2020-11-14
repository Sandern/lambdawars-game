from core.units import UnitInfo#, UnitBaseCombatHuman as BaseClass
from entities import entity
from vmath import Vector
from srcbase import IN_SPEED, IN_DUCK
from wars_game.units.citizen import UnitCitizen as BaseClass
from gameinterface import CPASAttenuationFilter
if isserver:
    from utils import UTIL_SetSize

@entity('zm_unit_survivor', networked=True)
class Survivor(BaseClass):
    def Precache(self):
        super(Survivor, self).Precache()
        
        self.PrecacheScriptSound('HL2Player.SprintNoPower')
        self.PrecacheScriptSound('HL2Player.SprintStart')

    def OnUserControl(self, player):
        super(Survivor, self).OnUserControl(player)

    def OnUserLeftControl(self, player):
        super(Survivor, self).OnUserLeftControl(player)
        
        if isserver:
            # Kill myself
            self.Remove()
            
    suitpower = 100
    def StartSprinting(self):
        if self.suitpower < 10:
            # Don't sprint unless there's a reasonable
            # amount of suit power.
            filter = CPASAttenuationFilter(self)
            filter.UsePredictionRules()
            self.EmitSoundFilter(filter, self.entindex(), "HL2Player.SprintNoPower")
            return

        filter = CPASAttenuationFilter(self)
        filter.UsePredictionRules()
        self.EmitSoundFilter(filter, self.entindex(), "HL2Player.SprintStart")

        self.mv.maxspeed = self.HL2_SPRINT_SPEED
        self.sprinting = True

    def StopSprinting(self):
        self.mv.maxspeed = self.HL2_NORM_SPEED
        self.sprinting = False
        
    def SetDuckedEyeOffset(self, duckFraction):
        unitinfo = self.unitinfo
        vDuckHullMin = unitinfo.crouchmins
        vStandHullMin = unitinfo.mins

        fMore = ( vDuckHullMin.z - vStandHullMin.z )

        vecDuckViewOffset = unitinfo.crouchviewoffset
        vecStandViewOffset = unitinfo.viewoffset
        temp = self.GetViewOffset()
        temp.z = ( ( vecDuckViewOffset.z - fMore ) * duckFraction ) + \
                    ( vecStandViewOffset.z * ( 1 - duckFraction ) )
        self.SetViewOffset( temp )

    def OnButtonsChanged(self, buttons, buttonschanged):
        ''' The player controlling this unit changed
            button states. '''
        if buttonschanged & IN_SPEED:
            if buttons & IN_SPEED:
                self.StartSprinting()
            else:
                self.StopSprinting()
        if buttonschanged & IN_DUCK:
            if buttons & IN_DUCK:
                if isserver:
                    self.crouching = True
                    UTIL_SetSize(self, self.unitinfo.crouchmins, self.unitinfo.crouchmaxs)
                self.SetViewOffset(self.unitinfo.crouchviewoffset)
            else:
                if isserver:
                    self.crouching = False
                    UTIL_SetSize(self, self.unitinfo.mins, self.unitinfo.maxs)
                self.SetViewOffset(self.unitinfo.viewoffset)
                
    def SelectSlot(self, slot):
        return False
                
    def ClientCommand(self, args):
        return False
                
    HL2_WALK_SPEED = 150
    HL2_NORM_SPEED = 190
    HL2_SPRINT_SPEED = 320
        
    maxspeed = HL2_NORM_SPEED
    
class SurvivorInfo(UnitInfo):
    name = 'zm_unit_survivor'
    cls_name = 'zm_unit_survivor'
    weapons = ['weapon_smg1']
    modelname = 'models/humans/group02/male_01.mdl'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    attributes = ['light']
    
    mins = Vector(-16, -16, 0)
    maxs = Vector( 16,  16,  72)
    crouchmins = Vector(-16, -16, 0)
    crouchmaxs = Vector( 16,  16,  36)
    viewoffset = Vector( 0, 0, 64)
    crouchviewoffset = Vector( 0, 0, 28)
    