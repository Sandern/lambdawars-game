from srcbase import *
from vmath import *
from core.units import UnitInfo, UnitBaseCombat as BaseClass, UnitVPhysicsLocomotion, UnitBaseAnimState
from entities import entity, CBeam, D_HT, D_FR, EFL_NO_DISSOLVE
from sound import CSoundEnvelopeController
from utils import UTIL_TraceHull, trace_t
from gameinterface import CPVSFilter, CPASAttenuationFilter, PrecacheMaterial
from te import te, CEffectData, DispatchEffect
from sound import CSoundParameters
from wars_game.statuseffects import StunnedEffectInfo
import random
if isserver:
    from utils import (ExplosionCreate, UTIL_DecalTrace, UTIL_PointContents, SF_ENVEXPLOSION_NOSPARKS,
                       SF_ENVEXPLOSION_NODLIGHTS, SF_ENVEXPLOSION_NOSMOKE, UTIL_DistApprox)
    from core.units import BaseAction

@entity('unit_rollermine', networked=True)
class UnitRollerMine(BaseClass):
    def Precache(self):
        super().Precache()
        
        self.PrecacheModel('models/roller_spikes.mdl')
        
        self.PrecacheModel( "sprites/bluelight1.vmt" )
        self.PrecacheModel( "sprites/rollermine_shock.vmt" )
        self.PrecacheModel( "sprites/rollermine_shock_yellow.vmt" )

        self.PrecacheScriptSound( "NPC_RollerMine.Taunt" )
        self.PrecacheScriptSound( "NPC_RollerMine.OpenSpikes" )
        self.PrecacheScriptSound( "NPC_RollerMine.Warn" )
        self.PrecacheScriptSound( "NPC_RollerMine.Shock" )
        self.PrecacheScriptSound( "NPC_RollerMine.ExplodeChirp" )
        self.PrecacheScriptSound( "NPC_RollerMine.Chirp" )
        self.PrecacheScriptSound( "NPC_RollerMine.ChirpRespond" )
        self.PrecacheScriptSound( "NPC_RollerMine.ExplodeChirpRespond" )
        self.PrecacheScriptSound( "NPC_RollerMine.JoltVehicle" )
        self.PrecacheScriptSound( "NPC_RollerMine.Tossed" )
        self.PrecacheScriptSound( "NPC_RollerMine.Hurt" )

        self.PrecacheScriptSound( "NPC_RollerMine.Roll" )
        self.PrecacheScriptSound( "NPC_RollerMine.RollWithSpikes" )
        self.PrecacheScriptSound( "NPC_RollerMine.Ping" )
        self.PrecacheScriptSound( "NPC_RollerMine.Held" )

        self.PrecacheScriptSound( "NPC_RollerMine.Reprogram" )

        PrecacheMaterial( "effects/rollerglow" )

        #gm_iszDropshipClassname = AllocPooledString( "npc_combinedropship" ) # For fast string compares.
        self.PrecacheScriptSound( "RagdollBoogie.Zap" )
        
    def CreateComponents(self):
        self.locomotion = self.LocomotionClass(self)

        self.animstate = self.AnimStateClass(self)
        
        # Server only
        if isserver:
            self.navigator = self.NavigatorClass(self)
            self.navigator.no_slow_down_to_target = True
            self.senses = self.SensesClass(self)
            self.CreateBehaviors()
            
        # Components that receive events
        if isserver:
            self.eventcomponents = [self.locomotion, self.navigator, self.animstate]
        else:
            self.eventcomponents = [self.locomotion, self.animstate]
            
        self.componentsinitalized = True
        
    if isserver:
        def Spawn(self):
            super().Spawn()
            
            self.SetSolid(SOLID_VPHYSICS)
            self.AddSolidFlags(FSOLID_FORCE_WORLD_ALIGNED | FSOLID_NOT_STANDABLE)
            
            self.AddEFlags(EFL_NO_DISSOLVE)
            
            self.SetBloodColor(DONT_BLEED)
            self.SetMoveType(MOVETYPE_VPHYSICS)
            
            self.SetRollerSkin()
            
            self.CreateVPhysics()
    else:
        def Spawn(self):
            super().Spawn()

            self.SetBloodColor(DONT_BLEED)

    def UpdateTranslateActivityMap(self):
        pass
        
    def CreateVPhysics(self):
        if self.buried:
            self.VPhysicsInitStatic()
            return True
        return self.BecomePhysical()

    def UnitThink(self):
        super().UnitThink()

        enemy = self.enemy
        if enemy:
            threshold = self.ROLLERMINE_OPEN_THRESHOLD

            self.mv.maxspeed = 4500

            # Open the spikes if i'm close enough to cut the enemy!!
            if not self.isopen and (self.EnemyDistance(enemy) <= threshold or not self.is_active):
                self.Open()
            elif self.isopen:
                dist = self.EnemyDistance(enemy)
                if dist >= threshold:
                    # Otherwise close them if the enemy is getting away!
                    self.Close()
                #elif self.EnemyInVehicle() && dist < self.ROLLERMINE_VEHICLE_HOP_THRESHOLD:
                #    # Keep trying to hop when we're ramming a vehicle, so we're visible to the player
                #    if ( vecVelocity.x != 0 && vecVelocity.y != 0 && flTorqueFactor > 3 && flDot > 0.0 )
                #        Hop( 300 )
        else:
            self.mv.maxspeed = 1500

            if self.isopen:
                self.Close()

    @property
    def is_active(self):
        return self.active_time > gpGlobals.curtime

    @property
    def isshocking(self):
        return gpGlobals.curtime < self.shocktime

    stun_delay = 3

    def Bury(self, tr):
        origin = self.GetAbsOrigin()
        UTIL_TraceHull(origin + Vector(0,0,64), origin - Vector( 0, 0, MAX_TRACE_LENGTH ), Vector(-16,-16,-16), Vector(16,16,16), MASK_NPCSOLID, self, self.GetCollisionGroup(), tr)

        #NDebugOverlay.Box( tr.startpos, Vector(-16,-16,-16), Vector(16,16,16), 255, 0, 0, 64, 10.0 )
        #NDebugOverlay.Box( tr.endpos, Vector(-16,-16,-16), Vector(16,16,16), 0, 255, 0, 64, 10.0 )

        # Move into the ground layer
        buriedPos = tr.endpos - Vector(0, 0, self.GetHullHeight() * 0.5)
        self.Teleport(buriedPos, None, vec3_origin)
        self.SetMoveType(MOVETYPE_NONE)

        #SetSchedule( SCHED_ROLLERMINE_BURIED_WAIT ) # TODO: event?
        
    def BecomePhysical(self):
        self.VPhysicsDestroyObject()

        self.RemoveSolidFlags(FSOLID_NOT_SOLID)

        # Setup the physics controller on the roller
        phys_obj = self.VPhysicsInitNormal(SOLID_VPHYSICS, self.GetSolidFlags(), False)

        if phys_obj is None:
            return False

        # Lomotion component acts as controller for VPhysics
        #self.locomotion.CreateMotionController()

        self.SetMoveType(MOVETYPE_VPHYSICS)

        phys_obj.Wake()

        return True
        
    def Open(self):
        # Friendly rollers cannot open
        if self.HasSpawnFlags(self.SF_ROLLERMINE_FRIENDLY):
            return

        if not self.isopen:
            self.SetModel("models/roller_spikes.mdl")
            self.SetRollerSkin()

            self.EmitSound("NPC_RollerMine.OpenSpikes")

            self.SetTouch(self.ShockTouch)
            self.isopen = True

            # Don't hop if we're constrained
            if not self.constraint:
                #if self.EnemyInVehicle():
                #    self.Hop( 256 )
                #elif not self.enemy or self.enemy.Classify() != CLASS_BULLSEYE ): # Don't hop when attacking bullseyes
                    self.Hop( 128 )
    
    def Close(self):
        # Not allowed to close while primed, because we're going to detonate on touch
        if self.isprimed:
            return

        if self.isopen and not self.isshocking:
            self.SetModel("models/roller.mdl")

            self.SetRollerSkin()

            self.SetTouch(None)
            self.isopen = False

            self.soundeventflags = self.ROLLERMINE_SE_CLEAR
        
    def SetRollerSkin(self):
        if self.powerdown == True:
            self.skin = self.ROLLER_SKIN_DETONATE
        #elif m_bHackedByAlyx == True:
        #    self.skin = self.ROLLER_SKIN_FRIENDLY
        else:
            self.skin = self.ROLLER_SKIN_REGULAR
    
    def SpikeTouch(self, other):
        pass
        
    def CloseTouch(self, pOther):
        if pOther.IsSolidFlagSet(FSOLID_TRIGGER | FSOLID_VOLUME_CONTENTS):
            return

        if self.isshocking:
            return

        bOtherIsDead = pOther.IsUnit() and not pOther.IsAlive()
        bOtherIsNotarget = ( pOther.GetFlags() & FL_NOTARGET ) != 0

        if not bOtherIsDead and not bOtherIsNotarget:
            disp = self.IRelationType(pOther)

            if disp == D_HT or disp == D_FR:
                self.ShockTouch(pOther)
                return

        self.Close()

    def EmbedTouch(self, pOther):
        if pOther.IsSolidFlagSet(FSOLID_TRIGGER | FSOLID_VOLUME_CONTENTS):
            return

        self.embedongroundimpact = False

        # Did we hit the world?
        if pOther.entindex() == 0:
            self.buried = True
            tr = trace_t()
            self.Bury(tr)

            # Destroy out physics object and become static
            self.VPhysicsDestroyObject()
            self.CreateVPhysics()

            # Drop a decal on the ground where we impacted
            UTIL_DecalTrace(tr, "Rollermine.Crater")

            # Make some dust
            #UTIL_CreateAntlionDust(tr.endpos, GetLocalAngles())

        # Don't try and embed again
        self.SetTouch(None)
        
    def ShockTarget(self, other):
        #if m_bHackedByAlyx:
        #    pBeam = CBeam.BeamCreate( "sprites/rollermine_shock_yellow.vmt", 4 )
        #else:
        pBeam = CBeam.BeamCreate( "sprites/rollermine_shock.vmt", 4 )

        startAttach = -1

        animating = other if hasattr(other, 'LookupAttachment') else None

        if pBeam is not None:
            pBeam.EntsInit(other, self)

            if animating:
                startAttach = animating.LookupAttachment("beam_damage")
                pBeam.SetStartAttachment(startAttach)

            # Change self up a little for first person hits
            if other.IsPlayer():
                pBeam.SetEndWidth( 8 )
                pBeam.SetNoise( 4 )
                pBeam.LiveForTime( 0.2 )
            else:
                pBeam.SetEndWidth( 16 )
                pBeam.SetNoise( 16 )
                pBeam.LiveForTime( 0.5 )
            
            pBeam.SetEndAttachment( 1 )
            pBeam.SetWidth( 1 )
            pBeam.SetBrightness( 255 )
            pBeam.SetColor( 255, 255, 255 )
            pBeam.RelinkBeam()
        
        shockPos = other.WorldSpaceCenter()

        if startAttach > 0 and animating:
            animating.GetAttachment( startAttach, shockPos )

        shockDir = (self.GetAbsOrigin() - shockPos)
        VectorNormalize(shockDir)

        filter = CPVSFilter(shockPos)
        te.GaussExplosion(filter, 0.0, shockPos, shockDir, 0)

    def ApplyKnockBack(self, target, dir, speed=250.0, stunchance=1.0, stunduration=1.34):
        """ Applies a knockback to the given target with a stun chance. """
        #curvel = target.GetAbsVelocity().LengthSqr()
        #if curvel < 2000.0 * 2000.0:
        #    target.ApplyAbsVelocityImpulse((dir * speed) + Vector(0, 0, 85))

        if target.IsUnit() and stunchance and random.random() < stunchance:
            StunnedEffectInfo.CreateAndApply(target, attacker=self, duration=stunduration)

    def ShockTouch(self, pOther):
        if pOther.IsSolidFlagSet(FSOLID_TRIGGER | FSOLID_VOLUME_CONTENTS):
            return

        if self.held or self.vehicle_stuck_to or gpGlobals.curtime < self.shocktime:
            return

        # error?
        assert not self.isprimed

        disp = self.IRelationType(pOther)

        # Ignore anyone that I'm friendly or neutral to.
        if disp != D_HT and disp != D_FR:
            return

        pPhysics = self.VPhysicsGetObject()

        # Calculate a collision force
        impulse = self.WorldSpaceCenter() - pOther.WorldSpaceCenter()
        impulse.z = 0
        VectorNormalize(impulse)
        impulse.z = 0.75
        VectorNormalize(impulse)
        impulse *= 600

        # Stun the roller
        self.active_time = gpGlobals.curtime + self.stun_delay

        # If we're a 'friendly' rollermine, just push the player a bit
        if self.HasSpawnFlags(self.SF_ROLLERMINE_FRIENDLY):
            if pOther.IsPlayer():
                vecForce = -impulse * 0.5
                pOther.ApplyAbsVelocityImpulse( vecForce )
            return

        # jump up at a 30 degree angle away from the guy we hit
        self.SetTouch(self.CloseTouch)
        pPhysics.SetVelocity(impulse, None)
        self.EmitSound("NPC_RollerMine.Shock")
        # Do a shock effect
        self.ShockTarget(pOther)

        self.shocktime = gpGlobals.curtime + 1.25

        # Calculate physics force
        out = Vector()
        pOther.CollisionProp().CalcNearestPoint(self.WorldSpaceCenter(), out)

        vecForce = ( -impulse * pPhysics.GetMass() * 10 )
        info = CTakeDamageInfo(self, self, vecForce, out, self.unitinfo.AttackMelee.damage, DMG_SHOCK)

        pOther.TakeDamage(info)

        self.ApplyKnockBack(pOther, vecForce, stunchance=1.0, speed=250)

        # Knock players back a bit
        if pOther.IsPlayer():
            vecForce = -impulse
            pOther.ApplyAbsVelocityImpulse( vecForce )

    def VPhysicsCollision(self, index, pEvent):
        # Make sure we don't keep hitting the same entity
        other_index = int(not index)
        other = pEvent.GetEnt(other_index)
        if pEvent.deltaCollisionTime < 0.5 and (other == self):
            return

        super().VPhysicsCollision(index, pEvent)

        # If we've just hit a vehicle, we want to stick to it
        '''if self.held or self.vehicle_stuck_to or !IsPlayerVehicle( pOther ):
            # Are we supposed to be embedding ourselves?
            if self.embedongroundimpact:
                # clear the flag so we don't queue more than once
                self.embedongroundimpact = False
                # call self when physics is done
                g_PostSimulationQueue.QueueCall( self, &CNPC_RollerMine.EmbedTouch, pOther )
            return

        StickToVehicle( pOther )'''
    
    def Hop(self, height):
        if self.nexthop > gpGlobals.curtime:
            return

        if self.GetMoveType() == MOVETYPE_VPHYSICS:
            pPhysObj = self.VPhysicsGetObject()
            pPhysObj.ApplyForceCenter(Vector(0,0,1) * height * pPhysObj.GetMass())
            
            angVel = AngularImpulse()
            angVel.Random( -400.0, 400.0 )
            pPhysObj.AddVelocity(None, angVel)

            self.nexthop = gpGlobals.curtime + self.ROLLERMINE_HOP_DELAY

    def PreDetonate(self):
        """ Makes warning noise before actual explosion occurs """
        if isserver:
            self.skin = 2
        self.Hop(300)

        self.SetTouch(None)
        self.SetThink(self.Explode)
        self.SetNextThink(gpGlobals.curtime + 0.5)

        self.EmitSound("NPC_RollerMine.Hurt")

    def Explode(self):
        self.takedamage = DAMAGE_NO

        #FIXME: Hack to make thrown mines more deadly and fun
        expDamage = 100 if self.isprimed else 25

        #If we've been hacked and we're blowing up cause we've been shut down then do moderate damage.
        if self.powerdown == True:
            expDamage = 70

        # Underwater explosion?
        if UTIL_PointContents(self.GetAbsOrigin(), MASK_WATER):
            data = CEffectData()
            data.origin = self.WorldSpaceCenter()
            data.magnitude = expDamage
            data.scale = 128
            data.flags = (SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSMOKE)
            DispatchEffect("WaterSurfaceExplosion", data)
        else:
            ExplosionCreate(self.WorldSpaceCenter(), self.GetLocalAngles(), self, expDamage, 160, True )

        info = CTakeDamageInfo(self, self, 1, DMG_GENERIC)
        self.Event_Killed(info)

        # Remove myself a frame from now to avoid doing it in the middle of running AI
        self.SetThink(self.SUB_Remove)
        self.SetNextThink(gpGlobals.curtime)
        
    def RollingSpeed(self):
        return self.GetAbsVelocity().Length()
        
    def UpdateRollingSound(self):
        if self.rollingsoundstate == self.ROLL_SOUND_NOT_READY:
            return

        soundState = self.ROLL_SOUND_OFF
        rollingSpeed = self.RollingSpeed()
        if rollingSpeed > 0:
            soundState = self.ROLL_SOUND_OPEN if self.isopen else self.ROLL_SOUND_CLOSED

        controller = CSoundEnvelopeController.GetController()
        params = CSoundParameters()
        if soundState == self.ROLL_SOUND_CLOSED:
            self.GetParametersForSound( "NPC_RollerMine.Roll", params, None )
        elif soundState == self.ROLL_SOUND_OPEN:
            self.GetParametersForSound( "NPC_RollerMine.RollWithSpikes", params, None )
        elif soundState == self.ROLL_SOUND_OFF:
            # no sound
            pass

        # start the new sound playing if necessary
        if self.rollingsoundstate != soundState:
            self.StopRollingSound()

            self.rollingsoundstate = soundState

            if self.rollingsoundstate == self.ROLL_SOUND_OFF:
                return

            filter = CPASAttenuationFilter( self )
            self.rollsound = controller.SoundCreate(filter, self.entindex(), params.channel, params.soundname, params.soundlevel)
            controller.Play( self.rollsound, params.volume, params.pitch )
            self.rollingsoundstate = soundState

        if self.rollsound:
            # for tuning
            #DevMsg("SOUND: %s, VOL: %.1f\n", self.rollingsoundstate == self.ROLL_SOUND_CLOSED ? "CLOSED" : "OPEN ", rollingSpeed )
            controller.SoundChangePitch( self.rollsound, params.pitchlow + (params.pitchhigh - params.pitchlow) * rollingSpeed, 0.1 )
            controller.SoundChangeVolume( self.rollsound, params.volume * rollingSpeed, 0.1 )

    def StopRollingSound(self):
        controller = CSoundEnvelopeController.GetController()
        controller.SoundDestroy( self.rollsound )
        self.rollsound = None

    def UpdatePingSound(self):
        pingSpeed = 0
        if self.isopen and not self.isshocking and not self.held:
            pEnemy = self.enemy
            if pEnemy:
                pingSpeed = self.EnemyDistance( pEnemy )
                pingSpeed = clamp( pingSpeed, 1, self.ROLLERMINE_OPEN_THRESHOLD )
                pingSpeed *= (1.0/self.ROLLERMINE_OPEN_THRESHOLD)

        if pingSpeed > 0:
            pingSpeed = 1-pingSpeed
            controller = CSoundEnvelopeController.GetController()
            params = CSoundParameters()
            self.GetParametersForSound( "NPC_RollerMine.Ping", params, None )
            if not self.pingsound:
                filter = CPASAttenuationFilter( self )
                self.pingsound = controller.SoundCreate( filter, self.entindex(), params.channel, params.soundname, params.soundlevel )
                controller.Play( self.pingsound, params.volume, 101 )

            controller.SoundChangePitch( self.pingsound, params.pitchlow + (params.pitchhigh - params.pitchlow) * pingSpeed, 0.1 )
            controller.SoundChangeVolume( self.pingsound, params.volume, 0.1 )
            #DevMsg("PING: %.1f\n", pingSpeed )
        else:
            self.StopPingSound()

    def StopPingSound(self):
        controller = CSoundEnvelopeController.GetController()
        controller.SoundDestroy(self.pingsound)
        self.pingsound = None

    def StopLoopingSounds(self):
        self.StopRollingSound()
        self.StopPingSound()
        super().StopLoopingSounds()

    def StartMeleeAttack(self, enemy):
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackMelee.attackspeed
        return False

    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionDie(BaseAction):
                def OnStart(self):
                    # Will remove the unit after explode:
                    self.outer.PreDetonate()

    customeyeoffset = Vector(0, 0, 8)

    # This are little 'sound event' flags. Set the flag after you play the
    # sound, and the sound will not be allowed to play until the flag is then cleared.
    ROLLERMINE_SE_CLEAR = 0x00000000
    ROLLERMINE_SE_CHARGE = 0x00000001
    ROLLERMINE_SE_TAUNT = 0x00000002
    ROLLERMINE_SE_SHARPEN = 0x00000004
    ROLLERMINE_SE_TOSSED = 0x00000008
    
    ROLLERMINE_HOP_DELAY = 2 # Don't allow hops faster than this
    ROLLERMINE_OPEN_THRESHOLD = 256
    
    SF_ROLLERMINE_FRIENDLY = (1 << 16)
    SF_ROLLERMINE_PROP_COLLISION = (1 << 17)
    
    ROLLER_SKIN_REGULAR = 0
    ROLLER_SKIN_FRIENDLY = 1
    ROLLER_SKIN_DETONATE = 2
    
    ROLL_SOUND_NOT_READY = 0
    ROLL_SOUND_OFF = 1 
    ROLL_SOUND_CLOSED = 2 
    ROLL_SOUND_OPEN = 3
        
    powerdown = False
    isopen = True
    isprimed = False
    shocktime = 0.0
    nexthop = 0.0
    pingsound = None
    rollsound = None
    rollingsoundstate = ROLL_SOUND_OFF
    soundeventflags = 0
    embedongroundimpact = False
    buried = False
    held = False
    active_time = 0
    vehicle_stuck_to = False

    selectionparticlename = 'unit_circle_simple_ground'

    constraint = None  # For sticking to vehicles

    LocomotionClass = UnitVPhysicsLocomotion
    AnimStateClass = UnitBaseAnimState

    cancappcontrolpoint = False

class RollerMineInfo(UnitInfo):
    name = 'unit_rollermine'
    cls_name = 'unit_rollermine'
    displayname = '#CombRollermine_Name'
    description = '#CombRollermine_Description' 
    image_name = 'vgui/combine/units/unit_combine_roller'
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    modelname = 'models/roller.mdl'
    hulltype = 'HULL_SMALL_CENTERED'
    zoffset = 28.0
    oncreatedroptofloor = False
    placeatmins = True
    maxspeed = 1200.0  # More like the angular speed
    health = 155
    population = 2
    buildtime = 14.0
    viewdistance = 640
    attributes = ['metal', 'mechanic', 'shock']
    costs = [[('requisition', 10), ('power', 10)], [('kills', 1)]]
    techrequirements = ['build_comb_armory']
    #sai_hint = set(['sai_unit_support'])

    class AttackMelee(UnitInfo.AttackMelee):
        maxrange = 0.0
        damage = 2
        attackspeed = 1.0
    attacks = 'AttackMelee'
