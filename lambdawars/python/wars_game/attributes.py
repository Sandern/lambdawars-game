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


class ChitinAttributeInfo(AttributeInfo):
    """ antlions that have natural hard carapace.
    """
    name = 'chitin'


class CreatureAttributeInfo(AttributeInfo):
    """ Units like Vortigaunts or Antlions and Zombies.
    """
    name = 'creature'
    dmgrecvmodifiers = {
        'molotovfire': ScaleBonusDamage(1.5),
    }


class SynthAttributeInfo(AttributeInfo):
    """ semi-organic armored Combine units like Hunter, Strider, Gunship.
    """
    name = 'synth'
	
    dmgmodifiers = {
        'medium': ConstantBonusDamage(4),
        'heavy': ConstantBonusDamage(3),

    }
    dmgrecvmodifiers = {
        'bullet': ScaleBonusDamage(0.25),
        'pulse': ScaleBonusDamage(0.25),
       # 'pulse_elite': ScaleBonusDamage(0.6),
       # 'plasma': ScaleBonusDamage(0.8),
       # 'explosive': ScaleBonusDamage(0.8),
       #'slash': ScaleBonusDamage(0.2),  # to take little damage from zombies and minor antlions
       # 'bite': ScaleBonusDamage(0.1),  # and headcrabs - now hunters will be more useful in Overrun
    }


class MetalAttributeInfo(AttributeInfo):
    """ for really heavy full metal units, like Dog and mb future Resistance Bulldozer/Combine Walking Wall.
    """
    name = 'metal'

    dmgmodifiers = {
        'medium': ConstantBonusDamage(8),
    }

    dmgrecvmodifiers = {
       'bullet': ScaleBonusDamage(0.5),
       'pulse': ScaleBonusDamage(0.5),
       #'plasma': ScaleBonusDamage(0.5),  # heaviest ones should not be too vulnerable to snipers
      # 'explosive': ScaleBonusDamage(0.7),
       # 'fire': ScaleBonusDamage(0.3),
       # 'slash': ScaleBonusDamage(0.1),  # to take little damage from zombies and minor antlions
       # 'bite': ScaleBonusDamage(0.1),  # and hardly damage from headcrabs
        'energyball': ScaleBonusDamage(1.0),
        #'mortar': ScaleBonusDamage(2.0),
    }


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
        'building': ConstantBonusDamage(70),
        'creature': ConstantBonusDamage(90),
        'synth': ConstantBonusDamage(100),
        'metal': ConstantBonusDamage(100),
        'heavy': ConstantBonusDamage(20),
    }


class SlashAttribute(AttributeInfo):
    name = 'slash'

    dmgmodifiers = {
        'light': ConstantBonusDamage(19),
        'medium': ConstantBonusDamage(5),
    }


class CrushAttribute(AttributeInfo):
    """ like Slash, but for really heavy melee attacks (e.g. Antlion Guard) dealing full damage to buildings, Synth
        and Metal units, unlike Slash and Bite
    """
    name = 'crush'

    dmgmodifiers = {
        'light': ConstantBonusDamage(30),
        'medium': ConstantBonusDamage(10),
    }


class BiteAttribute(AttributeInfo):
    name = 'bite'

    dmgmodifiers = {
        'light': ConstantBonusDamage(10),
        'building': ScaleBonusDamage(0.1),
    }


class BulletAttribute(AttributeInfo):
    name = 'bullet'

    dmgmodifiers = {
        'light': ConstantBonusDamage(4),
        # 'creature': ConstantBonusDamage(2),
    }


class PulseAttribute(AttributeInfo):
    name = 'pulse'

    dmgmodifiers = {
        'light': ConstantBonusDamage(4),
        'medium': ConstantBonusDamage(5),
        #'synth': ConstantBonusDamage(3),
        'metal': ConstantBonusDamage(3),
    }


class PulseShotgunAttribute(AttributeInfo):
    name = 'pulse_shotgun'  # for higher tier units, should probably name it "pulse_t3" instead

    dmgmodifiers = {
        'light': ConstantBonusDamage(20),
        'medium': ConstantBonusDamage(20),
    }


class PlasmaAttribute(AttributeInfo):
    """ dark energy plasma, for sniper """
    name = 'plasma'

    dmgmodifiers = {
        #'light': ConstantBonusDamage(20),
        'medium': ConstantBonusDamage(10),
        'heavy': ConstantBonusDamage(20),
        'building': ScaleBonusDamage(0.2),
        'defence': ScaleBonusDamage(1.5),
    }

class CrossbowAttribute(AttributeInfo):
    """ For veterans"""
    name = 'crossbow'

    dmgmodifiers = {
        'light': ConstantBonusDamage(40),
        'medium': ConstantBonusDamage(20),
        #'heavy': ConstantBonusDamage(20),
        'building': ScaleBonusDamage(0.2),
        'defence': ScaleBonusDamage(1.5),
    }


class ShockAttribute(AttributeInfo):
    name = 'shock'

    dmgmodifiers = {
        # 'heavy': ConstantBonusDamage(50),
        'building': ScaleBonusDamage(0.5),
        # 'synth': ScaleBonusDamage(0.5),
    }


class LaserAttribute(AttributeInfo):
    """ Lasers (e.g. stalker). """
    name = 'burn'

    dmgmodifiers = {
        'heavy': ConstantBonusDamage(1),
    }


class FireAttribute(AttributeInfo):
    """ Flame throwers. """
    name = 'fire'

    dmgmodifiers = {
        'light': ConstantBonusDamage(8),
        'medium': ConstantBonusDamage(8),
        'heavy': ConstantBonusDamage(8),
        'creature': ConstantBonusDamage(6),
        #'building': ConstantBonusDamage(6),
    }

    def ApplyToTarget(self, target, dmg_info):
        BurningEffectInfo.CreateAndApply(target, dietime=9.0, attacker=self.owner)  # increased burning duration


class MolotovFireAttribute(AttributeInfo):
    """ Molotov attack """
    name = 'molotovfire'

    def ApplyToTarget(self, target, dmg_info):
        BurningMolotovEffectInfo.CreateAndApply(target, dietime=2.0, attacker=self.owner)


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
    }


class ExplosiveMineAttribute(AttributeInfo):
    """ Mines only """
    name = 'explosive_mines'

    dmgmodifiers = {
        'light': ConstantBonusDamage(30),
        'medium': ConstantBonusDamage(15),
        #'building': ScaleBonusDamage(0.1),
    }


class EnergyBallAttribute(AttributeInfo):
    """ Attribute for Combine Elite energy ball. """
    name = 'energyball'


class DogSlamImpactAttribute(AttributeInfo):
    """ Attribute for Dog Slam & Jump abilities. """
    name = 'dogslamimpact'

    dmgmodifiers = {
		'synth': ConstantBonusDamage(200),
		'light': ConstantBonusDamage(50),
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
		'light': ScaleBonusDamage(1.8),
		'medium': ScaleBonusDamage(2.4),
		'heavy': ScaleBonusDamage(2.8),
		'synth': ScaleBonusDamage(3.0),
		'metal': ScaleBonusDamage(3.0),

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