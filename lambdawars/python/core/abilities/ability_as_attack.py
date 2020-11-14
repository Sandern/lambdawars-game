""" Provides boilerplate ability to use an ability as an unit attack.
"""
from core.abilities import AbilityTarget
from core.units import UnitInfo
from fields import StringField
from entities import MouseTraceData


class AbilityAsAttack(AbilityTarget):
    defaultautocast = True

    def DoAttack(self, unit, enemy):
        """ Called when doing the attack. Energy is taken at this point and the unit is in range. """
        unit.StartRangeAttack(enemy)

    if isserver:
        def DoAbility(self):
            data = self.mousedata

            target = data.ent if (data.ent and not data.ent.IsWorld()) else None

            for unit in self.units:
                # execute_attack argument is added when executed from the attack,
                # while the second path is when you actually execute the ability.
                # For now it's assumed this is the main attack (so the attack order results
                # in the executing of the ability attack).
                if self.kwarguments.get('execute_attack', False):
                    if self.TakeEnergy(unit):
                        self.DoAttack(unit, target)
                        self.SetRecharge(unit)
                elif target:
                        self.unit.AttackOrder(ability=self, enemy=target)

            self.Completed()


class AttackAbilityAsAttack(UnitInfo.AttackBase):
    abi_attack_name = StringField()

    def CanAttack(self, enemy):
        unit = self.unit
        if not unit.CanRangeAttack(enemy):
            return False
        abi = unit.abilitiesbyname[self.abi_attack_name]
        if not abi.CanAttack(unit, enemy):
            return False
        target_is_enemy = (unit.curorder and unit.curorder.type == unit.curorder.ORDER_ENEMY and
                           unit.curorder.target == enemy)
        return (target_is_enemy or unit.abilitycheckautocast[abi.uid]) and abi.CanDoAbility(None, unit=unit)

    def Attack(self, enemy, action):
        unit = self.unit
        leftpressed = MouseTraceData()
        leftpressed.ent = enemy
        unit.DoAbility(self.abi_attack_name, [('leftpressed', leftpressed)], autocasted=True, execute_attack=True)
        return True
