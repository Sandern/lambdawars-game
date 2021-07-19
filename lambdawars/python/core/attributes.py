""" Maps an attribute name to a class. """
import gamemgr
import random
from fields import LocalizedStringField
from vmath import Vector, QAngle, AngleVectors, VectorNormalize, DotProduct
    
# Attribute db
dbid = 'attributes'
dbattributes = gamemgr.dblist[dbid]
dbattributes.priority = 2 # Increase priority to ensure it registered before the units

# Attribute info entry
class AttributeInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __new__(cls, name, bases, dct):
        newcls = gamemgr.BaseInfoMetaclass.__new__(cls, name, bases, dct)
        
        if isclient:
            # Create description
            for k, v in newcls.dmgmodifiers.items():
                against = 'all' if k == None else k
                newcls.description += '    Against %s: %s\n' % (against, v.desc)
                
            for k, v in newcls.dmgrecvmodifiers.items():
                against = 'all' if k == None else k
                newcls.description += '    From %s: %s\n' % (against, v.desc)
                
            if newcls.description:
                newcls.description = newcls.name + '\n' + newcls.description
            
        return newcls


class AttributeInfo(gamemgr.BaseInfo, metaclass=AttributeInfoMetaClass):
    id = dbid
    
    #: Name shown in hud.
    #: In case the name starts with #, it is considered a localized string.
    displayname = LocalizedStringField(value='')
    
    description = ''

    #: Dictionary with damage modifiers against other attributes.
    dmgmodifiers = {}
    #: Dictionary with damage receive modifiers against other attributes.
    dmgrecvmodifiers = {}
    
    #: Owning unit
    owner = None
    
    #: Default order of attribute. Only relevant for dynamically added attributes.
    #: Only influences the place at which the attribute is displayed in the hud.
    order = 1000
    
    def __init__(self, unit):
        super().__init__()
        
        self.owner = unit

    #: Defines a method to custom apply logic to target. Receives the target and dmg info.
    ApplyToTarget = None
    #: Defines a method to custom apply logic to damage receiver. Receives the receiver and dmg info.
    ApplyToReceiver = None


def ConstantBonusDamage(damage):
    """ Helper to add a constant damage.

        Args:
            damage (float): bonus damage

        Returns:
            lambda: method to add contant damage, with description attached.
    """
    f = lambda dmg_info: dmg_info.AddDamage(damage)
    if damage < 0:
        f.desc = 'Damage reduction %s' % (-damage)
    else:
        f.desc = 'Bonus damage %s' % (damage)
    return f


def ScaleBonusDamage(scale):
    """ Helper to scale damage.

        Args:
            scale (float): scale value, ranging from 0 to 1

        Returns:
            lambda: method scaling the damage, with description attached.
    """
    f = lambda dmg_info: dmg_info.ScaleDamage(scale)
    if scale < 1.0:
        f.desc = 'Scales damage -%d%%' % (100 - scale*100)
    else:
        f.desc = 'Scales damage %d%%' % (scale*100)
    return f

def RandomBonusDamage(dmgmin, dmgmax):
    """  Helper to add random constant damage.

        Args:
            dmgmin (float): minimum value
            dmgmax (float): maximum value

        Returns:
            lambda: method to add random damage, with description attached.
    """
    f = lambda dmg_info: dmg_info.AddDamage(random.uniform(dmgmin,dmgmax))
    if dmgmin < 0:
        f.desc = 'Random damage set to 0' % (-dmgmin)
    elif dmgmax < 0:
        f.desc = 'Random maxdamage set to 0' % (-dmgmax)
    else:
        f.desc = 'Random damage between %f and %f' % (dmgmin, dmgmax)
    return f

# Core attributes
class BuildingAttributeInfo(AttributeInfo):
    name = 'building'
    
    dmgrecvmodifiers = { 
		'bullet': ScaleBonusDamage(0.15),
		'pulse': ScaleBonusDamage(0.30),
		'ar1': ScaleBonusDamage(0.35),
		'synth': ScaleBonusDamage(0.5),
		'pulse_shotgun': ScaleBonusDamage(0.30),
		'tau': ScaleBonusDamage(0.30),
		#'creature': ScaleBonusDamage(0.35),
		#'chitin': ScaleBonusDamage(2.86), # To compensate antlion damage
    }

class DefenceBuildingAttributeInfo(AttributeInfo):
    name = 'defence'
    
    dmgrecvmodifiers = { 
        'bullet': ScaleBonusDamage(0.25),
        'pulse': ScaleBonusDamage(0.3),
        'ar1': ScaleBonusDamage(0.35),
		'pulse_shotgun': ScaleBonusDamage(0.35),
        'explosive': ScaleBonusDamage(1.10),
		#'synth': ScaleBonusDamage(0.8),
        #'shock': ScaleBonusDamage(0.6),
    }

class CoverAttributeInfo(AttributeInfo):
    name = 'cover'
    
    dmgrecvmodifiers = { 
        None: ScaleBonusDamage(0.5),
    }

class CoverDirectionalAttributeInfo(AttributeInfo):
    name = 'cover_front'

    def ApplyToReceiver(self, receiver, dmg_info):
        # Get the cover spot
        cover_spot = receiver.cover_spot

        # Scale damage based on cover spot direction
        angles = QAngle(0, cover_spot.angle if cover_spot.type == 2 else receiver.GetAbsAngles().y, 0)
        forward = Vector()
        AngleVectors(angles, forward)

        vec_damage_force = dmg_info.GetDamageForce()
        VectorNormalize(vec_damage_force)
        dot = DotProduct(forward, -vec_damage_force)

        # Scale damage when shield is facing about 45 degrees
        if dot > 0.70:
            dmg_info.ScaleDamage(0.15)