from core.attributes import *
from wars_game.statuseffects import (BurningEffectInfo, BurningMolotovEffectInfo, StunnedEffectInfo,
                                     StinkBombSlowEffectInfo)


# Some base attributes that do nothing, but are used to classify units.
class LightAttributeInfo(AttributeInfo):
    name = 'light'


class MediumAttributeInfo(AttributeInfo):
    name = 'medium'


class HeavyAttributeInfo(AttributeInfo):
    name = 'heavy'

class LargeAttribute(AttributeInfo):
    name = 'large'

class ChitinAttributeInfo(AttributeInfo):
    """ antlions that have natural hard carapace.
    """
    name = 'chitin'


class CreatureAttributeInfo(AttributeInfo):
    """ Units like Vortigaunts or Antlions and Zombies.
    """
    name = 'creature'

    dmgmodifiers = {
        'synth': ScaleBonusDamage(0.2),
        'metal': ScaleBonusDamage(0.1),
        'building': ScaleBonusDamage(0.5),
        'defence': ScaleBonusDamage(0.75),
    }


class SynthAttributeInfo(AttributeInfo):
    """ semi-organic armored Combine units like Hunter, Strider, Gunship.
    """
    name = 'synth'

    dmgrecvmodifiers = {
        'bullet': ScaleBonusDamage(0.25),
        #'buckshot': ScaleBonusDamage(0.25),
        'pulse': ScaleBonusDamage(0.25),
        'ar1': ScaleBonusDamage(0.25),
    }


class MetalAttributeInfo(AttributeInfo):
    """ for really heavy full metal units, like Dog and mb future Resistance Bulldozer/Combine Walking Wall.
    """
    name = 'metal'

    dmgrecvmodifiers = {
        'bullet': ScaleBonusDamage(0.25),
        #'buckshot': ScaleBonusDamage(0.25),
        'pulse': ScaleBonusDamage(0.25),
        'ar1': ScaleBonusDamage(0.25),
    }

class FlechetteAttribute(AttributeInfo):
    name = 'flechette'

    dmgmodifiers = {
        'medium': ConstantBonusDamage(6),
        'large': ConstantBonusDamage(5),
    }

class PulseCannonAttribute(AttributeInfo):
    name = 'pulse_cannon'

    dmgmodifiers = {
        'light': ConstantBonusDamage(21),
        'medium': ConstantBonusDamage(16),
        'heavy': ConstantBonusDamage(16),
        'creature': ConstantBonusDamage(21),
    }

class TauCannonAttribute(AttributeInfo):
    name = 'tau'

    dmgmodifiers = {
        'synth': ConstantBonusDamage(24),
        'metal': ConstantBonusDamage(24),
        'heavy': ConstantBonusDamage(36),
    }

class TauCannonAltAttribute(AttributeInfo):
    name = 'tau_alt'

    def ApplyToTarget(self, target, dmg_info):
        if target.IsAlive() and getattr(target, 'isbuilding', False):
            dmg_info.ScaleDamage(0.5)

class BunkerAttributeInfo(AttributeInfo):
    """ For bunker buildings. """
    name = 'bunker'

    dmgrecvmodifiers = {
        'fire': ScaleBonusDamage(10.0),  # fire/flamers do a lot of damage
        'explosive': ScaleBonusDamage(0.4),  # bunkers protect units agenst explosions
        'energyball': ScaleBonusDamage(0.0),  # energy ball also does a lot of damage to units inside
        'plasma': ScaleBonusDamage(0.8),  # snipers also so a lot of damage
        'light': ScaleBonusDamage(0.5),  # light units do little damage
        'medium': ScaleBonusDamage(0.7),  # medium units do less damage
        'slash': ScaleBonusDamage(0.1),  # to take little damage from zombies and minor antlions
        'bite': ScaleBonusDamage(0.1),  # and hardly damage from headcrabs
        'mortar': ScaleBonusDamage(0.0), # should do no damage
    }

class AidAttributeInfo(AttributeInfo):
    """ For future use in combine aid stations. """
    name = 'medaid'

    dmgrecvmodifiers = {
        'fire': ScaleBonusDamage(0.6),
        'explosive': ScaleBonusDamage(0.4),
        'plasma': ScaleBonusDamage(0.4),
        'bullet': ScaleBonusDamage(0.4),
        'pulse': ScaleBonusDamage(0.5),
        'pulse_elite': ScaleBonusDamage(0.5),
    }

class MechanicAttributeInfo(AttributeInfo):
    name = 'mechanic'


# Weapon attributes
class RPGAttribute(AttributeInfo):
    name = 'rpg'

    dmgmodifiers = {
        'building': ConstantBonusDamage(125),
        'defence': ConstantBonusDamage(125),
        'synth': ConstantBonusDamage(275),
        'metal': ConstantBonusDamage(325),
        'heavy': ConstantBonusDamage(50),
    }


class SlashAttribute(AttributeInfo):
    name = 'slash'

    dmgmodifiers = {
        'light': ConstantBonusDamage(25),
        'creature': ConstantBonusDamage(30),
    }


class CrushAttribute(AttributeInfo):
    """ like Slash, but for really heavy melee attacks (e.g. Antlion Guard) dealing full damage to buildings, Synth
        and Metal units, unlike Slash and Bite
    """
    name = 'crush'

    dmgmodifiers = {
        'light': ConstantBonusDamage(200),
        'medium': ConstantBonusDamage(200),
        'creature': ConstantBonusDamage(200),
        'heavy': ConstantBonusDamage(100),
    }


class BiteAttribute(AttributeInfo):
    name = 'bite'

    dmgmodifiers = {
        'light': ConstantBonusDamage(50),
        'medium': ConstantBonusDamage(25),
        #'creature': ConstantBonusDamage(25),
        #'heavy': ConstantBonusDamage(15),
        #'building': ScaleBonusDamage(0.1),
    }



class BulletAttribute(AttributeInfo):
    name = 'bullet'

    dmgmodifiers = {
        'light': ConstantBonusDamage(6),
        # 'creature': ConstantBonusDamage(2),
    }


class BuckShotAttribute(AttributeInfo):
    name = 'buckshot'

    dmgmodifiers = {
        'light': ScaleBonusDamage(4),
        'creature': ScaleBonusDamage(4),
        'medium': ScaleBonusDamage(2.4),
    }

class WinchesterAttribute(AttributeInfo):
    name = 'winchester'

    dmgmodifiers = {
        'medium': ConstantBonusDamage(25),
        'creature': ConstantBonusDamage(50),
    }


class WinchesterAltAttribute(AttributeInfo):
    name = 'winchester_alt'

    dmgmodifiers = {
        'medium': ConstantBonusDamage(50),
        'creature': ConstantBonusDamage(100),
        'light': ConstantBonusDamage(12),
        'synth': ScaleBonusDamage(0.25),
        'metal': ScaleBonusDamage(0.25),
        'building': ScaleBonusDamage(0.15),
        'defence': ScaleBonusDamage(0.25),
    }

class PulseAttribute(AttributeInfo):
    name = 'pulse'

    dmgmodifiers = {
        'light': ConstantBonusDamage(4),
        'medium': ConstantBonusDamage(5),
    }

class AR1Attribute(AttributeInfo):
    name = 'ar1'

    dmgmodifiers = {
        'light': ConstantBonusDamage(7),
        'medium': ConstantBonusDamage(9),
        'heavy': ConstantBonusDamage(1),
        'creature': ConstantBonusDamage(1),
    }


class PulseShotgunAttribute(AttributeInfo):
    name = 'pulse_shotgun'

    dmgmodifiers = {
        #'light': ConstantBonusDamage(20),
        'medium': ScaleBonusDamage(1.5),
        #'synth': ConstantBonusDamage(20),
    }


class PlasmaAttribute(AttributeInfo):
    """ dark energy plasma, for sniper """
    name = 'plasma'

    dmgmodifiers = {
        'light': ConstantBonusDamage(200),
        'medium': ConstantBonusDamage(220),
        'heavy': ConstantBonusDamage(280),
        'creature': ConstantBonusDamage(50),
        'defence': ScaleBonusDamage(2.0),
    }

class CrossbowAttribute(AttributeInfo):
    """ For veterans"""
    name = 'crossbow'

    dmgmodifiers = {
        'light': ConstantBonusDamage(50),
        'medium': ConstantBonusDamage(100),
        'heavy': ConstantBonusDamage(100),
        #'synth': ConstantBonusDamage(50),
        'building': ScaleBonusDamage(0.5),
        'defence': ScaleBonusDamage(1.5),
    }


class ShockAttribute(AttributeInfo):
    name = 'shock'

    dmgmodifiers = {
        # 'heavy': ConstantBonusDamage(50),
        #'building': ScaleBonusDamage(0.5),
        'synth': ScaleBonusDamage(5),
        'metal': ScaleBonusDamage(10),
    }


class LaserAttribute(AttributeInfo):
    """ Lasers (e.g. stalker). """
    name = 'burn'

    dmgmodifiers = {
        'light': ConstantBonusDamage(1),
    }


class FireAttribute(AttributeInfo):
    """ Flame throwers. """
    name = 'fire'

    dmgmodifiers = {
        'light': ConstantBonusDamage(10),
        'medium': ConstantBonusDamage(10),
        'heavy': ConstantBonusDamage(2),
        'creature': ConstantBonusDamage(7),

        'building': ConstantBonusDamage(1),
        'defence': ConstantBonusDamage(2),
    }

    def ApplyToTarget(self, target, dmg_info):
        BurningEffectInfo.CreateAndApply(target, dietime=0.3, attacker=self.owner, attributes=self.owner.attributes)  # increased burning duration


class MolotovFireAttribute(AttributeInfo):
    """ Molotov attack """
    name = 'molotovfire'

    dmgmodifiers = {
        'creature': ConstantBonusDamage(4),
        'light': ConstantBonusDamage(3),
        'medium': ConstantBonusDamage(1),

        'building': ConstantBonusDamage(1),
        'defence': ConstantBonusDamage(2),
    }

    def ApplyToTarget(self, target, dmg_info):
        BurningMolotovEffectInfo.CreateAndApply(target, dietime=0.25, attacker=self.owner, attributes=self.owner.attributes)


class StinkBombAttribute(AttributeInfo):
    """ StinkBomb attack """
    name = 'stinkbomb'

    def ApplyToTarget(self, target, dmg_info):
        StinkBombSlowEffectInfo.CreateAndApply(target, duration=3.0, attacker=self.owner)


class AcidAttribute(AttributeInfo):
    """ Acid (e.g. Antlion Worker Spit). """
    name = 'acid'

    dmgmodifiers = {
        'light': ConstantBonusDamage(40),
        'medium': ConstantBonusDamage(25),
    }


class ExplosiveAttribute(AttributeInfo):
    """ Explosives, mines, etc. """
    name = 'explosive'

    dmgmodifiers = {
        'light': ScaleBonusDamage(2.0),
        'medium': ScaleBonusDamage(2.0),
        'heavy': ScaleBonusDamage(1.5),
        'synth': ScaleBonusDamage(0.25),
    }


class C4ExplosiveAttribute(AttributeInfo):
    """ C4 """
    name = 'c4explosive'

    dmgmodifiers = {
        #'building': ScaleBonusDamage(3.0),
    }

    def ApplyToTarget(self, target, dmg_info):
        if target.IsAlive() and getattr(target, 'isbuilding', False):
            dmg_info.ScaleDamage(3.0)

class ExplosiveCanisterAttribute(AttributeInfo):
    """ Headcrab Canisters """
    name = 'explosive_canister'

    dmgmodifiers = {
        'heavy': ScaleBonusDamage(0.8),
        'creature': ScaleBonusDamage(0.3),
        'building': ScaleBonusDamage(0.2),
        'synth': ScaleBonusDamage(0.15),
        'metal': ScaleBonusDamage(0.1),
    }


class EnergyBallAttribute(AttributeInfo):
    """ Attribute for Combine Elite energy ball. """
    name = 'energyball'
    dmgmodifiers = {
        'synth': ConstantBonusDamage(200),
    }


class DogSlamImpactAttribute(AttributeInfo):
    """ Attribute for Dog Slam & Jump abilities. """
    name = 'dogslamimpact'

    dmgmodifiers = {
        #'synth': ConstantBonusDamage(200),
        'large': ScaleBonusDamage(2.5),
        'light': ScaleBonusDamage(2.5),
        'medium': ScaleBonusDamage(2.5),
        'heavy': ScaleBonusDamage(1.5),
    }

    def ApplyToTarget(self, target, dmg_info):
        """ Makes this attribute do something to the target unit. """
        if target.IsAlive():
            StunnedEffectInfo.CreateAndApply(target, attacker=self.owner, duration=2)


class StunAttribute(AttributeInfo):
        name = 'stun'

        def ApplyToTarget(self, target, dmg_info):
            if target.IsAlive():
                StunnedEffectInfo.CreateAndApply(target, attacker=self.owner, duration=0.89)




class MortarAttribute(AttributeInfo):
    """ Attribute for Mortar """
    name = 'mortar'

    dmgmodifiers = {
        'metal': ScaleBonusDamage(0.5),
    }


# ======================================================================================================================
# =============================================== Squad Wars Attributes ================================================
# ======================================================================================================================

class CharAssaultAttribute(AttributeInfo):
    """ Assault attribute for Squad Wars gamemode """
    name = 'assault'

    dmgrecvmodifiers = {
        'dps': ScaleBonusDamage(0.75),
        'bite': ScaleBonusDamage(0.5),
        'slash': ScaleBonusDamage(0.4),
    }


class CharTankAttribute(AttributeInfo):
    """ Tank attribute, should receive least damage """
    name = 'tank'

    dmgrecvmodifiers = {
        'dps': ScaleBonusDamage(0.5),  # receive twice as less damage from DPS
        'bite': ScaleBonusDamage(0.2),  # able to stand against neutral enemies
        'fire': ScaleBonusDamage(0.7),  # able to stand fire damage better
        'slash': ScaleBonusDamage(0.2),  # able to stand against neutral enemies
        'energyball': ScaleBonusDamage(0.40),  # don't die from energy balls instantly
    }
    dmgmodifiers = {

    }


class CharMedicAttribute(AttributeInfo):
    """ Medic attribute, should deal least damage """
    name = 'medic'

    dmgrecvmodifiers = {
        'bite': ScaleBonusDamage(0.6),
        'slash': ScaleBonusDamage(0.6),
    }

    dmgmodifiers = {

    }


class CharScoutAttribute(AttributeInfo):
    """ Scout attribute, should receive more damage """
    name = 'scout'

    dmgrecvmodifiers = {
        'dps': ScaleBonusDamage(1.1),
        'bite': ScaleBonusDamage(0.6),
        'slash': ScaleBonusDamage(0.6),
    }

    dmgmodifiers = {

    }


class CharDPSAttribute(AttributeInfo):
    """ DPS attribute, should deal most damage """
    name = 'dps'

    dmgrecvmodifiers = {
        'bite': ScaleBonusDamage(0.8),
        'slash': ScaleBonusDamage(0.8),
        'assault': ScaleBonusDamage(1.2),
        'dps': ScaleBonusDamage(1.2),
    }

    dmgmodifiers = {
        'assault': ConstantBonusDamage(10),
        'creature': ConstantBonusDamage(20),

    }


class CharSupportAttribute(AttributeInfo):
    """ Support attribute, should be a bit tankier """
    name = 'support'

    dmgrecvmodifiers = {
        'dps': ScaleBonusDamage(0.6),
        'bite': ScaleBonusDamage(0.6),
        'slash': ScaleBonusDamage(0.6),
    }

    dmgmodifiers = {

    }


class CharBossAttribute(AttributeInfo):
    name = 'boss'

    dmgrecvmodifiers = {
        'bullet': ScaleBonusDamage(0.5),
        'dps': ScaleBonusDamage(0.8),
        'energyball': ScaleBonusDamage(0.33),
        'rpg': ScaleBonusDamage(1.5),
    }