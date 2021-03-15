from vmath import Vector
from core.abilities import AbilityThrowObject
from entities import MouseTraceData
from core.units import UnitInfo
import random


class AbilityThrowMolotov(AbilityThrowObject):
    # Info
    name = "throwmolotov"
    rechargetime = 2.5
    #energy = 35.0
    displayname = "#RebThrowMolotov_Name"
    description = "#RebThrowMolotov_Description"
    image_name = 'VGUI/rebels/abilities/molotov.vmt'
    throwanimation = 'ANIM_THROWGRENADE'
    throw_anim_speed = 2.25
    throwrange = 640
    throwspeed = 933
    predict_target_position = False
    throwstartattachment = 'anim_attachment_LH'
    useanimationevent = True
    objectclsname = 'molotov'
    defaultautocast = True
    autocast_exclude = ['throwstinkbomb']
    
    #def SetupObject(self, throwobject):
    #    super().SetupObject(throwobject)

    def SelectUnits(self):
        return self.SelectGroupUnits()

    def GetTossStartAndEnd(self, unit):
        start, end = super().GetTossStartAndEnd(unit)
        end = Vector(end)
        #end.x += random.uniform(-48.0, 48.0)
        #end.y += random.uniform(-48.0, 48.0)
        return start, end
        
    allowmultipleability = True


class MolotovAttack(UnitInfo.AttackBase):
    #damage = 80
    #damagetype = DMG_SHOCK
    minrange = 0.0
    maxrange = 640.0
    attackspeed = AbilityThrowMolotov.rechargetime
    cone = 0.7
    attributes = ['molotovfire']
    
    def CanAttack(self, enemy):
        unit = self.unit
        if not unit.abilitycheckautocast[unit.abilitiesbyname[AbilityThrowMolotov.name].uid]:
            return False
        return unit.CanRangeAttack(enemy) and AbilityThrowMolotov.CanDoAbility(None, unit=unit)
        
    def Attack(self, enemy, action):
        unit = self.unit
        leftpressed = MouseTraceData()
        leftpressed.ent = enemy
        leftpressed.groundendpos = enemy.GetAbsOrigin()
        leftpressed.endpos = enemy.GetAbsOrigin()
        unit._throwabi_throwmolotov_asattack = True
        unit.DoAbility(AbilityThrowMolotov.name, [('leftpressed', leftpressed)])
        unit._throwabi_throwmolotov_asattack = False
        return True

AbilityThrowMolotov.autocast_attack = MolotovAttack