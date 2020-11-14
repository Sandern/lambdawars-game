from srcbase import *
from vmath import *
from core.units import UnitInfo, UnitBaseCombat as BaseClass
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity

if isserver:
    from entities import (gEntList, ImpulseScale, CalculateExplosiveDamageForce,
                          CTakeDamageInfo, CalculateMeleeDamageForce)
    from utils import (CTraceFilterMelee, trace_t, Ray_t, UTIL_TraceRay)

@entity('npc_dota_base', networked=True)
class UnitDota(BaseClass):
    precachesoundlist = [
        "Shoot",
        "LightQuiet",
        "Heavy",
        "Spawn",
        "Footstep",
        "Shockwave",
        "Destruction",
        "Bash",
        "ManaBurn",
        "Heal",
        "FrostArmor",
        "Whip",
        "Roar",
        "RaiseDead",
        "PreAttack",
        "Tornado",
        "Grunt",
        "Cast",
        "ChainLighting",
        "Slam",
        "Death",
        "Attack",
        "Ensnare",
        "Light",
        "SummonTornado",
        "Staff",
        "Move",
        "Roquelaire",
        "ProjectileImpact",
        "Clap",
        "Stomp",
    ]

    def CanBecomeRagdoll(self):
        return False
    
    def CreateComponents(self):
        super().CreateComponents()
        
        self.locomotion.stepsize = 24.0
    
    def KeyValue(self, key, value):
        if key == 'unittype':
            return False
        if key == 'MapUnitName':
            self.SetUnitType(value)
            return True
        return super().KeyValue(key, value)
        
    @classmethod
    def PrecacheUnitType(cls, info):
        super().PrecacheUnitType(info)
        
        soundset = getattr(info, 'SoundSet', None)
        if soundset:
            for sound in cls.precachesoundlist:
                cls.PrecacheSound('%s.%s' % (soundset, sound))
    
    if isserver:
        def StartMeleeAttack(self, enemy):
            # Do melee damage
            self.MeleeAttack() 
                
            return super().StartMeleeAttack(enemy)

    def OnUnitTypeChanged(self, oldunittype):
        super().OnUnitTypeChanged(oldunittype)
        
        self.soundset = getattr(self.unitinfo, 'SoundSet', None) 
        
        HealthBarOffset = getattr(self.unitinfo, 'HealthBarOffset', None)
        if HealthBarOffset:
            colprop = self.CollisionProp()
            self.barsoffsetz = HealthBarOffset - (colprop.OBBMaxs().z - colprop.OBBMins().z)
            
    def MeleeAttack(self):
        #target = self.enemy
        #if not target:
        #    return
        
        attackinfo = self.unitinfo.AttackMelee
        damage = attackinfo.damage
        
        # If the target's still inside the shove cone, ensure we hit him
        # vecForward = Vector()
        # vecEnd = Vector()
        # AngleVectors( self.GetAbsAngles(), vecForward )
        # flDistSqr = ( target.WorldSpaceCenter() - self.WorldSpaceCenter() ).LengthSqr()
        # v2LOS = ( target.WorldSpaceCenter() - self.WorldSpaceCenter() ).AsVector2D()
        # Vector2DNormalize(v2LOS)
        # flDot	= DotProduct2D (v2LOS, vecForward.AsVector2D() )
        # if flDistSqr < (self.attackinfo.maxrange*self.attackinfo.maxrange) and flDot >= self.ANTLIONGUARD_MELEE1_CONE:
            # vecEnd = target.WorldSpaceCenter()
        # else:
        vecEnd = self.WorldSpaceCenter() + (self.BodyDirection3D() * attackinfo.maxrange)

        # Use the melee trace to ensure we hit everything there
        tr = trace_t()
        dmgInfo = CTakeDamageInfo(self, self, damage, attackinfo.damagetype)
        traceFilter = CTraceFilterMelee( self, Collision_Group_t.COLLISION_GROUP_NONE, dmgInfo, 1.0, True )
        ray = Ray_t()
        ray.Init( self.WorldSpaceCenter(), vecEnd, Vector(-40,-40, -120), Vector(40, 40, 120)) #Vector(-16,-16,-16), Vector(16,16,16) ) # <- Use a rather big ray to ensure we hit something. It's really annoying to see it hit the air.
        UTIL_TraceRay( ray, MASK_SHOT_HULL, traceFilter, tr ) 
        pHurt = tr.ent

        if pHurt:
            traceDir = ( tr.endpos - tr.startpos )
            VectorNormalize( traceDir )

            # Generate enough force to make a 75kg guy move away at 600 in/sec
            vecForce = traceDir * ImpulseScale(75, 600)
            info = CTakeDamageInfo(self, self, vecForce, tr.endpos, damage, DMG_CLUB)
            pHurt.TakeDamage( info )

            #self.EmitSound("NPC_AntlionGuard.Shove")
            
        # Knock things around
        self.ImpactShock(tr.endpos, 512.0, 2500.0)
        
    def ImpactShock(self, origin, radius, magnitude, ignored = None):
        # Also do a local physics explosion to push objects away
        vecSpot = Vector()
        falloff = 1.0 / 2.5

        entity = None

        # Find anything within our radius
        
        while True:
            entity = gEntList.FindEntityInSphere( entity, origin, radius )
            if entity == None:
                break
            # Don't affect the ignored target
            if entity == ignored:
                continue
            if entity == self:
                continue

            # UNDONE: Ask the object if it should get force if it's not MOVETYPE_VPHYSICS?
#if entity.GetMoveType() == MOVETYPE_VPHYSICS or ( entity.VPhysicsGetObject() and entity.IsPlayer() == False ):
            vecSpot = entity.BodyTarget( self.GetAbsOrigin(), True )
            
            # decrease damage for an ent that's farther from the bomb.
            flDist = ( self.GetAbsOrigin() - vecSpot ).Length()

            if radius == 0 or flDist <= radius:
                adjustedDamage = flDist * falloff
                adjustedDamage = magnitude - adjustedDamage
        
                if adjustedDamage < 1:
                    adjustedDamage = 1

                if entity.IsUnit():
                    dir = (vecSpot - self.GetAbsOrigin())
                    dist = VectorNormalize(dir)
                    entity.ApplyAbsVelocityImpulse((dir * (1.0/dist) * 2.0) + Vector(0,0,75))

                info = CTakeDamageInfo(self, self, adjustedDamage, DMG_BLAST)
                CalculateExplosiveDamageForce(info, (vecSpot - self.GetAbsOrigin()), self.GetAbsOrigin())

                entity.VPhysicsTakeDamage(info)

    def PlaySound(self, soundname):
        if not self.soundset:
            return
        self.EmitSound('%s.%s' % (self.soundset, soundname))
        
    #def MoveSound(self):
    #    self.PlayOrderSound('%s.Move' % (self.soundset));
            
    #def AttackSound(self):
    #    self.PlayOrderSound(self.unitinfo.sound_attack)
            
    def DeathSound(self):
        self.PlaySound('Death')
        
    def HandlePlaySoundAttack(self, event):
        self.PlaySound('Attack')
                
    # Vars
    maxspeed = 290.0
    yawspeed = 40.0
    jumpheight = 40.0
    attackmelee1act = 'ACT_DOTA_ATTACK'
    
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_DOTA_IDLE',
        'ACT_DOTA_IDLE_RARE',
        'ACT_DOTA_ATTACK',
        'ACT_DOTA_RUN',
        'ACT_DOTA_CAST_ABILITY_1',
        'ACT_DOTA_CAST_ABILITY_2',
        'ACT_DOTA_CAST_ABILITY_3',
        'ACT_DOTA_CAST_ABILITY_4',
        'ACT_DOTA_CAST_ABILITY_5',
        'ACT_DOTA_CAST_ABILITY_6',
        'ACT_DOTA_DISABLED',
        'ACT_DOTA_DIE',
        'ACT_DOTA_CAPTURE',
        'ACT_DOTA_FLAIL',
        'ACT_DOTA_CHANNEL_ABILITY_1',
        'ACT_DOTA_CHANNEL_ABILITY_2',
        'ACT_DOTA_CHANNEL_ABILITY_3',
        'ACT_DOTA_CHANNEL_ABILITY_4',
        'ACT_DOTA_CHANNEL_ABILITY_5',
        'ACT_DOTA_CHANNEL_ABILITY_6',
    ] )

    # Animation translation table
    acttables = {
        Activity.ACT_IDLE : 'ACT_DOTA_IDLE',
        Activity.ACT_RUN : 'ACT_DOTA_RUN',
        Activity.ACT_MELEE_ATTACK1 : 'ACT_DOTA_ATTACK',
        Activity.ACT_DIESIMPLE : 'ACT_DOTA_DIE',
        Activity.ACT_MP_JUMP : 'ACT_DOTA_FLAIL',
        Activity.ACT_MP_JUMP_FLOAT : 'ACT_DOTA_FLAIL',
    }
    
    if isserver:
        aetable = dict(BaseClass.aetable)
        aetable.update({
            'AE_DOTA_PLAY_SOUND_ATTACK' : 'HandlePlaySoundAttack',
        })
    
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=180.0,
        bodyyawnormalized=True,
        leganimtype=LegAnimType_t.LEGANIM_9WAY,
        invertposeparameters=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super().__init__(outer, animconfig)
            self.newjump = False
            
        def OnNewModel(self):
            super().OnNewModel()

            studiohdr = self.outer.GetModelPtr()
            
            self.turn = self.outer.LookupPoseParameter("turn")
            if self.turn >= 0:
                self.outer.SetPoseParameter(self.turn, 0.0)
                self.bodyyaw = self.turn
                
    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass): 
            # Many of the die animations cause crashes in Alien Swarm engine (something in the bone setup).
            # Just disable it.
            class ActionDie(BaseClass.BehaviorGenericClass.ActionDie):
                def OnStart(self):
                    outer = self.outer
                    if outer.unitinfo.name.find('creep') != -1:
                        outer.SetThink(outer.SUB_Remove, gpGlobals.curtime)
                        return self.Continue()
                    return super().OnStart()
                
# Register unit
class UnitDotaInfo(UnitInfo):
    abilities = {
        8 : "attackmove",
        9 : "holdposition",
    }
    
    class AttackMelee(UnitInfo.AttackMelee):
        maxrange = 150.0
        damage = 50
        damagetype = DMG_SLASH
        attackspeed = 1.6
    attacks = 'AttackMelee'
    