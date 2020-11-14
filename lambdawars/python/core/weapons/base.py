"""Provides a python base for weapons."""
from entities import CWarsWeapon as BaseClass
from core.units import UnitInfo
from kvdict import LoadFileIntoDictionaries
from gamerules import GetAmmoDef
from fow import FogOfWarMgr

class WarsWeaponBase(BaseClass):
    """ Base for weapons."""
    def __init__(self):
        super().__init__()
        
        attackprimary = self.AttackPrimary
        if attackprimary:
            self.UpdateAttackSettings(attackprimary)
            
        if isclient:
            self.SetOverrideClassname(self.clientclassname)
            
    def UpdateAttackSettings(self, attackprimary):
        self.firerate = attackprimary.attackspeed
        self.maxrange1 = attackprimary.maxrange
        self.overrideammodamage = attackprimary.damage
        self.maxbulletrange = attackprimary.maxrange + 128.0 # Note: we allow bullets to travel a bit further, so they are not cut off directly
        self.enableburst = attackprimary.usesbursts
        self.minburst = attackprimary.minburst
        self.maxburst = attackprimary.maxburst
        self.minresttime = attackprimary.minresttime
        self.maxresttime = attackprimary.maxresttime
        self.primaryattackattributes = attackprimary.attributes
        
    def UpdateEnemyTransmissionInfo(self, owner, enemy):
        if enemy:
            FogOfWarMgr().ForceTransmitUpdateEntity(owner, enemy.GetOwnerNumber())
            return [enemy.GetAbsOrigin()]
        return []
            
    def StartRangeAttack(self, enemy):
        """ Called by units to do a range attack. """
        owner = self.GetOwner()
        enemyorigins = self.UpdateEnemyTransmissionInfo(owner, enemy)
        owner.DoAnimation(owner.ANIM_ATTACK_PRIMARY, extraorigins=enemyorigins)
        owner.nextattacktime = gpGlobals.curtime + self.firerate
        self.PrimaryAttack()
        return False

    def StartMeleeAttack(self, enemy):
        """ Called by units to do a melee attack. """
        owner = self.GetOwner()
        enemyorigins = self.UpdateEnemyTransmissionInfo(owner, enemy)
        owner.DoAnimation(owner.ANIM_MELEE_ATTACK1, extraorigins=enemyorigins)
        owner.nextattacktime = gpGlobals.curtime + self.firerate
        self.PrimaryAttack()
        return False
        
    @classmethod    
    def InitEntityClass(cls):
        super().InitEntityClass()
        
        wpndata = LoadFileIntoDictionaries('scripts/%s.txt'% (cls.clientclassname))

        if wpndata:
            # Fill in the damage and damagetype for attacks (mainly used in the hud)
            # TODO: Maybe get rid of weapon scripts, since modifying the python code is just as easy?
            if cls.AttackPrimary:
                try:
                    primaryammo = wpndata['primary_ammo']
                    idx = GetAmmoDef().Index(primaryammo)
                except KeyError:
                    idx = -1
                    
                if idx != -1:
                    class AttackPrimary(cls.AttackPrimary):
                        name = cls.AttackPrimary.name
                        modname = cls.AttackPrimary.modname
                        if cls.AttackPrimary.damage == 0:
                            damage = GetAmmoDef().PlrDamage(idx)
                        if cls.AttackPrimary.damagetype == 0:
                            damagetype = GetAmmoDef().DamageType(idx)
                    cls.AttackPrimary = AttackPrimary
            
            if cls.AttackSecondary:
                try:
                    secondaryammo = wpndata['secondary_ammo']
                    idx = GetAmmoDef().Index(secondaryammo)
                except KeyError:
                    idx = -1
                
                if idx != -1:
                    class AttackSecondary(cls.AttackSecondary):
                        name = cls.AttackPrimary.name
                        modname = cls.AttackPrimary.modname
                        if cls.AttackSecondary.damage == 0:
                            damage = GetAmmoDef().PlrDamage(idx)
                        if cls.AttackSecondary.damagetype == 0:
                            damagetype = GetAmmoDef().DamageType(idx)
                    cls.AttackSecondary = AttackSecondary
            
        # Store it, just in case you want it somewhere..
        cls.wpndata = wpndata
        
    #: Overrides class name on the client. Used to read out the correct weapon script.
    clientclassname = None
    #: Used to directly cause a muzzle event, since we don't play weapon animations.
    muzzleoptions = None 

    # Aliases
    AttackBase = UnitInfo.AttackBase
    AttackRange = UnitInfo.AttackRange
    AttackMelee = UnitInfo.AttackMelee

    # Added to the list of units attacks in UnitBaseCombat.RebuildAttackInfo (if not None)
    AttackPrimary = None
    AttackSecondary = None
