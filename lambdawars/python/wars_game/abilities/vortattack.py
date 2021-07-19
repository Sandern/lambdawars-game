from srcbase import DMG_SHOCK
from core.abilities import AbilityTargetGroup
from entities import MouseTraceData
from core.units import UnitInfo

class AbilityVortAttack(AbilityTargetGroup):
    # Info
    name = "vortattack"
    displayname = "#RebVortAtt_Name"
    description = "#RebVortAtt_Description"
    image_name = 'vgui/rebels/abilities/vortattack'
    hidden = True
    energy = 9
    rechargetime = 2.0
    defaultautocast = True
    
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata

            target = data.ent if (data.ent and not data.ent.IsWorld()) else None

            do_attack = self.kwarguments.get('vortattack', False)
            for unit in self.units:
                if do_attack:
                    if self.TakeEnergy(unit):
                        unit.DoAnimation(unit.ANIM_RANGE_ATTACK1)
                        self.SetRecharge(unit)
                else:
                    if target:
                        unit.AttackOrder(ability=self, enemy=target)
                    
            self.Completed()

class VortAttack(UnitInfo.AttackBase):
    damage = 60
    damagetype = DMG_SHOCK
    minrange = 0.0
    maxrange = 768.0
    attackspeed = AbilityVortAttack.rechargetime
    cone = 0.7
    
    def CanAttack(self, enemy):
        unit = self.unit
        #if not unit.abilitycheckautocast[unit.abilitiesbyname[AbilityVortAttack.name].uid]:
        #    return False
        target_is_enemy = (unit.curorder and (unit.curorder.type == unit.curorder.ORDER_ENEMY or unit.curorder.type == unit.curorder.ORDER_ABILITY and 
                           (unit.curorder.ability.name == 'attackmove' or unit.curorder.ability.name == 'vortattack')) and
                           unit.curorder.target == enemy)
        return unit.CanRangeAttack(enemy) and AbilityVortAttack.CanDoAbility(None, unit=unit) and (target_is_enemy or unit.abilitycheckautocast[unit.abilitiesbyname[AbilityVortAttack.name].uid])
        
    def Attack(self, enemy, action):
        unit = self.unit
        leftpressed = MouseTraceData()
        leftpressed.ent = enemy
        unit.DoAbility(AbilityVortAttack.name, [('leftpressed', leftpressed)], vortattack=True)
        return True