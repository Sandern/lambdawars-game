from vmath import Vector
from particles import PrecacheParticleSystem, PATTACH_ABSORIGIN_FOLLOW
from entities import entity
from core.buildings import UnitBaseBuilding as BaseClass

if isserver:
    from entities import D_LI, CreateEntityByName, DispatchSpawn
    from core.ents import CTriggerArea
    from utils import UTIL_SetSize, UTIL_SetOrigin, UTIL_Remove
    
if isserver:
    @entity('trigger_heal_area')
    class HealArea(CTriggerArea):
        def Precache(self):
            super().Precache()
            #PrecacheParticleSystem('pg_heal')
        
        def Spawn(self):
            self.Precache()
            
            super().Spawn()

            self.SetThink(self.HealThink, gpGlobals.curtime, 'HealThink')


        def Heal(self, unit, heal):
            """
            @type unit: core.units.base.UnitBase
            @type heal: float
            """
            # Must not be mechanic
            if 'mechanic' in unit.attributes:
                return
                
            if unit.health < unit.maxhealth:
                self.healing = True
                unit.health += min(heal, (unit.maxhealth-unit.health))
                #DispatchParticleEffect("pg_heal", PATTACH_ABSORIGIN_FOLLOW, entity)
                if hasattr(unit, 'EFFECT_DOHEAL'):
                    unit.DoAnimation(unit.EFFECT_DOHEAL)
                        
        def HealThink(self):

            dt = gpGlobals.curtime - self.GetLastThink('HealThink')
            heal = int(round(dt * self.healrate))

            self.healing = False

            for entity in self.touchingents:
                if not entity:
                    continue
                #heal units inside bunkers
                if entity.IsUnit() and entity.isbuilding and entity.unitinfo.name in ['build_comb_bunker','overrun_build_comb_bunker','build_reb_bunker','overrun_build_reb_bunker']:
                    for unit in entity.units:
                        self.Heal(unit,heal)
                    
                if not entity.IsUnit() or entity.isbuilding or entity.IRelationType(self) != D_LI:
                    continue
                
                self.Heal(entity,heal)

            self.SetNextThink(gpGlobals.curtime + 0.5, 'HealThink')
            
        #: Heal rate per second of this building
        healrate = 4
        #: Whether or not the area was healing units last think
        healing = False

@entity('build_baseregeneration', networked=True)
class BaseRegeneration(BaseClass):
    if isserver:
        def Precache(self):
            super().Precache()
            
            PrecacheParticleSystem(self.rangerangeparticlename)
            
        def Spawn(self):
            super().Spawn()

            zmin = self.WorldAlignMins().z
            zmax = self.WorldAlignMaxs().z
            origin = self.GetAbsOrigin()
            origin.z += zmin
            
            self.healarea = CreateEntityByName('trigger_heal_area')
            self.healarea.startdisabled = True
            self.healarea.SetOwnerNumber(self.GetOwnerNumber())
            UTIL_SetOrigin(self.healarea, origin)
            UTIL_SetSize(self.healarea, -Vector(self.healradius, self.healradius, -zmin), Vector(self.healradius, self.healradius, zmax))
            DispatchSpawn(self.healarea)
            self.healarea.SetOwnerEntity(self)
            self.healarea.SetParent(self)
            self.healarea.Activate()
            self.UpdateHealAreaState()
            
            #import ndebugoverlay
            #ndebugoverlay.EntityBounds(self.healarea, 255, 0, 0, 255, 10.0)

        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            if self.healarea:
                UTIL_Remove(self.healarea)
        
    def SetConstructionState(self, state):
        super().SetConstructionState(state) 
        
        self.UpdateHealAreaState()
        
    def UpdateHealAreaState(self):
        if self.healarea:
            if self.constructionstate == self.BS_CONSTRUCTED:
                self.healarea.Enable()
            else:
                self.healarea.Disable()
        
    def OnChangeOwnerNumber(self, oldownernumber):
        super().OnChangeOwnerNumber(oldownernumber)
        
        if self.healarea:
            self.healarea.SetOwnerNumber(self.GetOwnerNumber())
            
    if isclient:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.DisableRangeRadiusOverlay()

        def EnableRangeRadiusOverlay(self):
            if self.rangerangeoverlay:
                return
            mins = self.CollisionProp().OBBMins()
            range = self.healradius
            self.rangerangeoverlay = self.ParticleProp().Create(self.rangerangeparticlename, PATTACH_ABSORIGIN_FOLLOW, -1, Vector(0, 0, mins.z))
            self.rangerangeoverlay.SetControlPoint(4, self.GetTeamColor())
            self.rangerangeoverlay.SetControlPoint(2, Vector(range, 0, 0))
            
        def DisableRangeRadiusOverlay(self):
            if not self.rangerangeoverlay:
                return
            self.ParticleProp().StopEmission(self.rangerangeoverlay, False, False, True)
            self.rangerangeoverlay = None
        
        def OnSelected(self, player):
            super().OnSelected(player)
            
            self.EnableRangeRadiusOverlay()
        
        def OnDeSelected(self, player):
            super().OnDeSelected(player)
            
            self.DisableRangeRadiusOverlay()
        
    healarea = None
    autoconstruct = False
    healradius = 256
    
    rangerangeparticlename = 'range_radius_health'
    rangerangeoverlay = None

@entity('passive_regeneration', networked=True)
class PassiveRegeneration(BaseClass):
    if isserver:
        def Precache(self):
            super().Precache()

            PrecacheParticleSystem(self.rangerangeparticlename)

        def Spawn(self):
            super().Spawn()

            zmin = self.WorldAlignMins().z
            zmax = self.WorldAlignMaxs().z
            origin = self.GetAbsOrigin()
            origin.z += zmin

            self.healarea = CreateEntityByName('trigger_heal_area')
            self.healarea.startdisabled = False
            self.healarea.SetOwnerNumber(self.GetOwnerNumber())
            UTIL_SetOrigin(self.healarea, origin)
            UTIL_SetSize(self.healarea, -Vector(self.healradius, self.healradius, -zmin),
                         Vector(self.healradius, self.healradius, zmax))
            DispatchSpawn(self.healarea)
            self.healarea.SetOwnerEntity(self)
            self.healarea.SetParent(self)
            self.healarea.Activate()
            self.UpdateHealAreaState()

            # import ndebugoverlay
            # ndebugoverlay.EntityBounds(self.healarea, 255, 0, 0, 255, 10.0)

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            if self.healarea:
                UTIL_Remove(self.healarea)

        if isclient:
            def UpdateOnRemove(self):
                super().UpdateOnRemove()

                self.DisableRangeRadiusOverlay()

            def EnableRangeRadiusOverlay(self):
                if self.rangerangeoverlay:
                    return
                mins = self.CollisionProp().OBBMins()
                range = self.healradius
                self.rangerangeoverlay = self.ParticleProp().Create(self.rangerangeparticlename,
                                                                    PATTACH_ABSORIGIN_FOLLOW, -1, Vector(0, 0, mins.z))
                self.rangerangeoverlay.SetControlPoint(4, self.GetTeamColor())
                self.rangerangeoverlay.SetControlPoint(2, Vector(range, 0, 0))

            def DisableRangeRadiusOverlay(self):
                if not self.rangerangeoverlay:
                    return
                self.ParticleProp().StopEmission(self.rangerangeoverlay, False, False, True)
                self.rangerangeoverlay = None

            def OnSelected(self, player):
                super().OnSelected(player)

                self.EnableRangeRadiusOverlay()

            def OnDeSelected(self, player):
                super().OnDeSelected(player)

                self.DisableRangeRadiusOverlay()

    healarea = None
    healradius = 256

    rangerangeparticlename = 'range_radius_health'
    rangerangeoverlay = None