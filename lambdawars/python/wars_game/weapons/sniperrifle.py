from srcbase import MASK_SOLID, COLLISION_GROUP_NONE, COLLISION_GROUP_BREAKABLE_GLASS
from vmath import Vector
from entities import entity, FireBulletsInfo_t, WeaponSound
from core.weapons import WarsWeaponBase, VECTOR_CONE_1DEGREES
from core.abilities import AbilityAsAttack, AttackAbilityAsAttack
from core.units import UnitInfo
from wars_game.abilities.steadyposition import AbilitySteadyPosition
from particles import PrecacheParticleSystem
from utils import UTIL_TraceLine, trace_t, CWarsBulletsFilter

if isclient:
    from particles import CNewParticleEffect


@entity('weapon_sniperrifle', networked=True)
class WeaponSniperRifle(WarsWeaponBase):
    def __init__(self):
        super().__init__()

        self.minrange1 = 0.0
        self.maxrange1 = 2048.0
        self.minrange2 = 0.0
        self.maxrange2 = 2048.0
        self.firerate = 3.5  # Initial attack speed
        self.bulletspread = VECTOR_CONE_1DEGREES

    def Precache(self):
        super().Precache()

        PrecacheParticleSystem(self.trailfxname)
        self.sHaloSprite = self.PrecacheModel("sprites/light_glow03.vmt")

    def PrimaryAttack(self):
        owner = self.GetOwner()

        owner.DoMuzzleFlash()

        self.SendWeaponAnim(self.GetPrimaryAttackActivity())

        # self.clip1 = self.clip1 - 1

        vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()

        # NOTE: Do not use nextprimaryattack for attack time sound, otherwise it fades out too much. (since this is not per frame)
        self.WeaponSound(WeaponSound.SINGLE, gpGlobals.curtime)
        self.nextprimaryattack = gpGlobals.curtime + self.firerate

        info = FireBulletsInfo_t()
        info.shots = 1
        info.vecsrc = vecShootOrigin
        info.vecdirshooting = vecShootDir
        info.vecspread = self.bulletspread
        info.distance = self.maxbulletrange
        info.ammotype = self.primaryammotype
        info.tracerfreq = 0
        info.damage = self.AttackPrimary.damage
        info.attributes = self.primaryattackattributes

        if isserver:
            trace_filter = CWarsBulletsFilter(owner, COLLISION_GROUP_BREAKABLE_GLASS)
            trace_filter.SetPassEntity(owner.garrisoned_building or self)
            
            fire_origin = Vector()
            self.GetAttachment('lazer', fire_origin)
            end = vecShootOrigin + vecShootDir * self.maxrange1
            tr = trace_t()
            UTIL_TraceLine(fire_origin, end, MASK_SOLID, trace_filter, tr)
        
            self.SendMessage([
                self.SNIPERFX_BEAM,
                fire_origin,
                tr.endpos,
            ])
            
        owner.FireBullets(info)
        if isserver:
            owner.DispatchEvent('OnOutOfClip')
        
    SNIPERFX_BEAM = 1

    def ReceiveMessage(self, msg):
        msgtype = msg[0]
        if msgtype == self.SNIPERFX_BEAM:
            self.DispatchFireTrail(msg[1], msg[2])

    def MakeTracer(self, vectracersrc, tr, tracertype):
        pass # Tracer is already created in PrimaryAttack
        
    def DispatchFireTrail(self, start, end):
        trail_fx = CNewParticleEffect.CreateOrAggregate(None, self.trailfxname, start, None)
        if trail_fx and trail_fx.IsValid():
            owner = self.GetOwner()
            trail_fx.SetControlPoint(0, start)
            trail_fx.SetControlPoint(1, end)
            trail_fx.SetControlPoint(2, owner.GetTeamColor())
        
    clientclassname = 'weapon_sniperrifle'
    muzzleoptions = 'SHOTGUN MUZZLE'
    trailfx = None
    trailfxname = 'pg_sniper_muzzle'

    '''
    class AttackPrimary(WarsWeaponBase.AttackBase):
        damage = 100
        damagetype = DMG_BULLET
        minrange = 150.0
        maxrange = 1470.0
        #cone = 0.7
        cone = UnitInfo.AttackRange.DOT_1DEGREE
        attackspeed = AbilityMarkmanShot.rechargetime
        attributes = ['plasma']

        def CanAttack(self, enemy):
            unit = self.unit
            if not unit.CanRangeAttack(enemy):
                return False
            try:
                if not unit.insteadyposition:
                    abi = unit.abilitiesbyname[AbilitySteadyPosition.name]
                    return unit.abilitycheckautocast[abi.uid] and abi.CanDoAbility(None, unit=unit)
                abi = unit.abilitiesbyname[AbilityMarkmanShot.name]
                targetisenemey = unit.curorder and unit.curorder.type == unit.curorder.ORDER_ENEMY and unit.curorder.target == enemy
                return (targetisenemey or unit.abilitycheckautocast[abi.uid]) and abi.CanDoAbility(None, unit=unit)
            except KeyError:
                PrintWarning('weapon_sniperrifle: unit %s incorrectly setup for sniper rifle\n' % (unit))
            return False

        def Attack(self, enemy, action):
            unit = self.unit
            if action and not unit.insteadyposition:
                ability = unit.DoAbility(AbilitySteadyPosition.name, [], autocasted=True, direct_from_attack=True)
                return action.SuspendFor(ActionDoSteadyPosition, 'Changing to steady position', ability, None)

            leftpressed = MouseTraceData()
            leftpressed.ent = enemy
            unit.DoAbility(AbilityMarkmanShot.name, [('leftpressed', leftpressed)], autocasted=True, markmanshot=True)
            return True
    '''

    class AttackPrimary(AttackAbilityAsAttack):
        abi_attack_name = 'marksmanshot'
        maxrange = 1408.0
        attackspeed = 2.25
        damage = 20
        cone = UnitInfo.AttackRange.DOT_3DEGREE
        attributes = ['plasma']

        def CanAttack(self, enemy):
            unit = self.unit
            if unit.CanRangeAttack(enemy) and unit.unitinfo.sniperenemy:
                return True

            if not unit.CanRangeAttack(enemy):
                return False

            if not unit.insteadyposition:
                abi = unit.abilitiesbyname[AbilitySteadyPosition.name]
                return unit.abilitycheckautocast[abi.uid] and abi.CanDoAbility(None, unit=unit)

            abi = unit.abilitiesbyname[self.abi_attack_name]
            target_is_enemy = (unit.curorder and (unit.curorder.type == unit.curorder.ORDER_ENEMY or unit.curorder.type == unit.curorder.ORDER_ABILITY 
                               and (unit.curorder.ability.name == 'attackmove' or unit.curorder.ability.name == self.abi_attack_name)) and
                               unit.curorder.target == enemy)
            return (target_is_enemy or unit.abilitycheckautocast[abi.uid]) and abi.CanDoAbility(None, unit=unit)

        def Attack(self, enemy, action):
            unit = self.unit
            # First go into steady position when needed, except when garrisoned in a building.
            if action and not unit.insteadyposition and not unit.garrisoned and not unit.unitinfo.sniperenemy:
                ability = unit.DoAbility(AbilitySteadyPosition.name, [], autocasted=True, direct_from_attack=True)
                return ability and action.SuspendFor(ability.ActionDoSteadyPosition, 'Changing to steady position',
                                                     ability, None)
            return super().Attack(enemy, action)


class AbilityMarkmanshot(AbilityAsAttack):
    name = 'marksmanshot'
    displayname = '#CombMarkmanShot_Name'
    description = '#CombMarkmanShot_Description'
    image_name = 'vgui/combine/abilities/marksmanshot'
    hidden = True
    rechargetime = 2.25

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)

        # if unit is garrisoned then ability still should be controllable
        if unit.garrisoned:
            requirements.discard('uncontrollable')

        if not getattr(unit, 'insteadyposition', False) and not unit.garrisoned and not unit.unitinfo.sniperenemy:
            requirements.add('steadyposition')
        return requirements