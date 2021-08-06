from srcbase import SOLID_BBOX, FSOLID_NOT_STANDABLE, FSOLID_NOT_SOLID, EF_NOSHADOW, SOLID_NONE
from vmath import Vector, QAngle, vec3_origin
from core.abilities import AbilityTarget, AbilityInstant
from core.units import CreateUnit, UnitBase, UnitInfo, GetUnitInfo
from entities import entity, FOWFLAG_UNITS_MASK, MouseTraceData
from fields import FloatField

if isserver:
    from core.units import UnitCombatSense


@entity('unit_scan', networked=True)
class Scan(UnitBase):
    def ShouldDraw(self):
        return False
        
    def IsSelectableByPlayer(self, player, target_selection):
        return False
        
    def GetIMouse(self):
        return None
        
    if isserver:
        def Spawn(self):
            super().Spawn()
            
            self.SetSolid(SOLID_NONE)
            self.AddSolidFlags(FSOLID_NOT_STANDABLE|FSOLID_NOT_SOLID)
            self.AddEffects(EF_NOSHADOW)
            self.SetCanBeSeen(False)
            
            self.senses = UnitCombatSense(self)
            
            self.SetThink(self.ScanThink, gpGlobals.curtime)
            
        def Restore(self, save):
            self.senses = UnitCombatSense(self)
        
            return super().Restore(save)
            
        def UpdateOnRemove(self):
            # ALWAYS CHAIN BACK!
            super().UpdateOnRemove()
            
            del self.senses
        
        def ScanThink(self):
            self.senses.PerformSensing()
            self.SetNextThink(gpGlobals.curtime + 0.1)
            
        def SetScanDuration(self, scanduration=10.0):
            self.SetThink(self.SUB_Remove, gpGlobals.curtime + scanduration, 'ScanDuration')

    fowflags = FOWFLAG_UNITS_MASK
    detector = True
    
class UnitScanInfo(UnitInfo):
    name = 'unit_scan'
    cls_name = 'unit_scan'
    viewdistance = 896.0
    health = 0
    minimaphalfwide = 0 # Don't draw on minimap
    population = 0
    resource_category = ''
    
class AbilityScan(AbilityTarget):
    # Info
    name = "scan"
    displayname = "#RebScan_Name"
    description = "#RebScan_Description"
    image_name = 'vgui/rebels/abilities/scan'
    hidden = True
    energy = 15
    rechargetime = 2.0
    scanduration = FloatField(value=10.0)
    scanrange = FloatField(value=896.0)
    activatesoundscript = 'ability_scan'
    maxrange = FloatField(value=8192.0)
    
    # For autocast
    supportsautocast = True
    defaultautocast = False
    lastpos = Vector(0, 0, 0)
    energyOffset = 30 # Needs the required energy plus this to trigger autocast
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata

            targetpos = data.endpos
            startpos = self.unit.GetAbsOrigin()
            #dist = startpos.DistTo(targetpos)
            dist = targetpos - startpos

            if (dist.x*dist.x + dist.y*dist.y)**0.5 > self.maxrange: 
                self.Cancel(cancelmsg='#Ability_OutOfRange', debugmsg='must be fired within range')
                return
            
            if not self.ischeat:
                if not self.TakeEnergy(self.unit):
                    self.Cancel()
                    return

            pos = data.groundendpos
            pos.z += 512.0

            self.lastpos.x = pos.x
            self.lastpos.y = pos.y
            self.lastpos.z = pos.z
            self.canState = True
            
            unit = CreateUnit('unit_scan', pos, owner_number=self.player.GetOwnerNumber())
            unit.viewdistance = self.scanrange
            unit.SetScanDuration(self.scanduration)
            self.Completed()
    
    @classmethod
    def SetupOnUnit(info, unit):
        super(AbilityScan, info).SetupOnUnit(unit)
        
    @classmethod
    def OnUnitThink(info, unit):
        if not unit.AllowAutoCast() or not unit.abilitycheckautocast[info.uid]:
            return

        if info.lastpos.x != 0 and info.lastpos.y != 0 and info.lastpos.z != 0 and unit.energy > (info.energy+info.energyOffset):
            leftpressed = MouseTraceData()
            leftpressed.endpos.x = info.lastpos.x
            leftpressed.endpos.y = info.lastpos.y
            leftpressed.endpos.z = info.lastpos.z
                
            leftpressed.groundendpos.x = info.lastpos.x
            leftpressed.groundendpos.y = info.lastpos.y
            leftpressed.groundendpos.z = info.lastpos.z
                
            unit.DoAbility(info.name, mouse_inputs=[('leftpressed', leftpressed)])
          
    def UpdateParticleEffects(self, inst, targetpos):
        inst.SetControlPoint(0, self.unit.GetAbsOrigin() + self.particleoffset)
        inst.SetControlPoint(2, Vector(self.maxrange, self.maxrange, 0))
        inst.SetControlPoint(4, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
    infoparticles = ['range_radius']
class AbilityOverrunScan(AbilityScan):
    name = 'overrun_scan'
    rechargetime = 0.0

class AbilityCharScan(AbilityScan):
    name = 'scan_char'
    displayname = "#MetroScan_Name"
    description = "#MetroScan_Description"
    energy = 20
    rechargetime = 10.0
    scanrange = FloatField(value=600.0)
