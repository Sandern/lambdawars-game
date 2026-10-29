"""Abilities that function as unit attacks.

Provides base classes for abilities that are used as unit attacks,
integrating with the unit combat system. These abilities can be
autocast and are triggered when units engage enemies in combat.
"""
from core.abilities import AbilityTarget
from core.units import UnitInfo
from fields import StringField
from entities import MouseTraceData


class AbilityAsAttack(AbilityTarget):
    """Base class for abilities that function as unit attacks.
    
    These abilities integrate with the unit combat system and can be
    triggered automatically when units engage enemies. The ability
    handles both manual activation and autocast scenarios.
    """
    defaultautocast = True

    def DoAttack(self, unit, enemy):
        """Called when executing the attack.
        
        Energy is taken at this point and the unit is in range.
        Override to customize attack behavior.
        
        Args:
            unit: Unit performing the attack.
            enemy: Target enemy entity.
        """
        unit.StartRangeAttack(enemy)

    if isserver:
        def DoAbility(self):
            """Execute the ability as an attack.
            
            Handles both direct ability execution and attack-triggered
            execution. If execute_attack is True, immediately performs
            the attack. Otherwise queues an attack order.
            """
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
    """Attack implementation that uses an ability for the attack.
    
    Wraps an ability so it can be used as a unit's primary attack.
    The ability is executed when the unit attacks an enemy.
    """
    abi_attack_name = StringField()

    def CanAttack(self, enemy):
        """Check if the unit can attack the enemy using this ability.
        
        Validates range, ability availability, and autocast conditions.
        
        Args:
            enemy: Target enemy entity.
            
        Returns:
            bool: True if the attack can be performed, False otherwise.
        """
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
        """Execute the attack by triggering the associated ability.
        
        Creates mouse trace data for the enemy and executes the ability
        with the execute_attack flag set to immediately perform the attack.
        
        Args:
            enemy: Target enemy entity.
            action: Attack action object (unused).
            
        Returns:
            bool: Always returns True to indicate attack was executed.
        """
        unit = self.unit
        leftpressed = MouseTraceData()
        leftpressed.ent = enemy
        unit.DoAbility(self.abi_attack_name, [('leftpressed', leftpressed)], autocasted=True, execute_attack=True)
        return True
