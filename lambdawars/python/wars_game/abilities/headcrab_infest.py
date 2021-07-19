from vmath import Vector, QAngle
from core.abilities import AbilityInstant
from core.units import CreateUnit, UnitBaseCombatHuman
from particles import DispatchParticleEffect, PrecacheParticleSystem

if isserver:
    from utils import UTIL_RemoveImmediate
    
    from achievements import ACHIEVEMENT_WARS_INFESTATION
    from playermgr import ListPlayersForOwnerNumber
    from wars_game.achievements import IsCommonGameMode

class AbilityHeadcrabInfest(AbilityInstant):
    name = 'headcrab_infest'
    displayname = '#HeadcrabInfest_Name'
    description = '#HeadcrabInfest_Description'
    hidden = True

    @classmethod
    def Precache(info):
        super().Precache()
        
        PrecacheParticleSystem("blood_impact_zombie_01")

    @classmethod
    def PreSpawnZombie(cls, zombie):
        zombie.BehaviorGenericClass = zombie.BehaviorRoamingClass

    @classmethod
    def TryTurnUnitInZombie(cls, inflictor, target):
        """ Tries to turn the target unit into a zombie, caused by the inflictor.
            
            The inflictor and target units are removed if zombification is successful.
            A new unit is spawned in place.
            
            This method is manually called from wars_game.units.headcrab.
        """
        if not target or not target.IsUnit():
            return False
            
        # Only human derived units
        if not isinstance(target, UnitBaseCombatHuman):
            return False
            
        # Don't try turning units with a huge max health into zombies
        if target.maxhealth > 400:
            return False
            
        # Must be less health than 30%
        if target.HealthFraction() > 0.3:
            return False
            
        ownernumber = inflictor.GetOwnerNumber()
        position = target.GetAbsOrigin()
        angles = target.GetAbsAngles()
        
        # Allow unit types to override the zombie unit to be spawned
        # e.g. Combine soldiers turn into Zombines
        zombietype_to = getattr(inflictor.unitinfo, 'infest_to_zombietype', 'unit_zombie')
        zombietype = getattr(target.unitinfo, 'infest_zombietype', zombietype_to)
        #print(zombietype_to, zombietype)
        if not zombietype:
            return False
            
        DispatchParticleEffect("blood_impact_zombie_01", target.WorldSpaceCenter(), QAngle(0, 0, 0))
        DispatchParticleEffect("blood_impact_zombie_01", target.WorldSpaceCenter() + Vector(0, 0, 40.0), QAngle(0, 0, 0))
        
        launcher_owner = getattr(inflictor, 'launcher_owner', None)
        
        UTIL_RemoveImmediate(inflictor)
        UTIL_RemoveImmediate(target)
        infestedzombie = CreateUnit(zombietype, position=position, angles=angles, owner_number=ownernumber,
                                    fnprespawn=cls.PreSpawnZombie)
        
        if infestedzombie:
            infestedzombie.EmitSound('Zombie.Alert')
            infestedzombie.uncontrollable = True
            
        if launcher_owner is not None and IsCommonGameMode():
            for player in ListPlayersForOwnerNumber(launcher_owner):
                player.AwardAchievement(ACHIEVEMENT_WARS_INFESTATION)
        
        return True

    if isserver:
        def DoAbility(self):
            if not self.SelectSingleUnit():
                self.Cancel(cancelmsg='No unit for ability')
                return
            
            self.Completed()
    else:
        def DoAbility(self):
            self.SelectSingleUnit()