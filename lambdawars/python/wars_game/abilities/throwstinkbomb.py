from vmath import Vector
from core.abilities import AbilityThrowObject, AbilityTarget
from entities import MouseTraceData
from core.units import UnitInfo

import random

class AbilityThrowStinkBomb(AbilityThrowObject):
    # Info
    name = "throwstinkbomb"
    rechargetime = 1.82
    #energy = 35.0
    displayname = "#RebThrowStinkbomb_Name"
    description = "#RebThrowStinkbomb_Description"
    image_name = 'vgui/rebels/abilities/stinkbomb.vmt'
    throwanimation = 'ANIM_THROWGRENADE'
    throw_anim_speed = 2.25
    predict_target_position = True
    throwstartattachment = 'anim_attachment_LH'
    useanimationevent = True
    objectclsname = 'stinkbomb'
    #defaultautocast = True
    supportsautocast = True
    autocast_exclude = ['throwmolotov']
    sai_hint = AbilityTarget.sai_hint | set(['sai_grenade'])

    def SelectUnits(self):
        return self.SelectGroupUnits()

    def GetTossStartAndEnd(self, unit):
        start, end = super().GetTossStartAndEnd(unit)
        end = Vector(end)
        end.x += random.uniform(-100.0, 100.0)
        end.y += random.uniform(-100.0, 100.0)
        return start, end
        
    allowmultipleability = True


class StinkBombAttack(UnitInfo.AttackBase):
    minrange = 0.0
    maxrange = 896.0
    attackspeed = AbilityThrowStinkBomb.rechargetime
    cone = 0.7
    attributes = ['stinkbomb']
    
    def CanAttack(self, enemy):
        unit = self.unit
        if not unit.abilitycheckautocast[unit.abilitiesbyname[AbilityThrowStinkBomb.name].uid]:
            return False
        return unit.CanRangeAttack(enemy) and AbilityThrowStinkBomb.CanDoAbility(None, unit=unit)
        
    def Attack(self, enemy, action):
        unit = self.unit
        leftpressed = MouseTraceData()
        leftpressed.ent = enemy
        leftpressed.groundendpos = enemy.GetAbsOrigin()
        leftpressed.endpos = enemy.GetAbsOrigin()
        unit._throwabi_throwstinkbomb_asattack = True
        unit.DoAbility(AbilityThrowStinkBomb.name, [('leftpressed', leftpressed)])
        unit._throwabi_throwstinkbomb_asattack = False
        return True

AbilityThrowStinkBomb.autocast_attack = StinkBombAttack

class AbilityThrowStinkBombChar(AbilityThrowStinkBomb):
    name = 'char_throwstinkbomb'
    rechargetime = 10.0
    throw_anim_speed = 3.0
    supportsautocast = False
