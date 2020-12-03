from srcbase import *
from vmath import *
from entities import entity
from .basehelicopter import BaseHelicopter as BaseClass, UnitBaseHelicopterAnimState
from core.units import UnitInfo, CreateUnitFancy
from gameinterface import CPASAttenuationFilter, CPASFilter
from utils import UTIL_PlayerByIndex
from sound import CSoundEnvelopeController
from entities import CBasePlayer, CreateEntityByName
from te import te, TE_EXPLFLAG_NOPARTICLES
from fields import UpgradeField, FloatField

if isserver:
    from utils import (UTIL_PrecacheOther, UTIL_Remove, UTIL_SetSize, UTIL_ScreenShake, ExplosionCreate, 
                       SF_ENVEXPLOSION_NODAMAGE, SF_ENVEXPLOSION_NOSPARKS, SF_ENVEXPLOSION_NODLIGHTS, 
                       SF_ENVEXPLOSION_NOSMOKE, SHAKE_START)
    from entities import CTakeDamageInfo, CPhysicsProp, SmokeTrail, CEntityFlame, PropBreakablePrecacheAll

import random
    
if isserver:
    @entity('prop_dropship_container')
    class CombineDropshipContainer(CPhysicsProp):
        def Precache(self):
            self.PrecacheModel(self.DROPSHIP_CONTAINER_MODEL)

            # Set this here to quiet base prop warnings
            self.SetModel(self.DROPSHIP_CONTAINER_MODEL)
            
            self.indexfireball = self.PrecacheModel('sprites/zerogxplode.vmt')

            super().Precache()
                
            for chunkmodelname in self.chunkmodelnames:
                self.PrecacheModel(chunkmodelname)
            for gibmodelname in self.gibmodelnames:
                self.PrecacheModel(gibmodelname)
            
            PropBreakablePrecacheAll(self.GetModelName())
        
        def Spawn(self):
            # NOTE: Model must be set before spawn
            self.SetModel(self.DROPSHIP_CONTAINER_MODEL)
            #self.SetSolid(SOLID_VPHYSICS)

            self.SetSolid(SOLID_NONE)
            self.SetSolidFlags(FSOLID_NOT_SOLID)
            #self.AddSolidFlags(FSOLID_NOT_SOLID)

            super().Spawn()

            self.health = self.maxhealth = 150 #sk_dropship_container_health.GetFloat()


            if self.lifetime != 0:
                self.SetThink(self.Remove, gpGlobals.curtime + self.lifetime, 'SelfDestructThink')
        
        def ShouldTriggerDamageEffect(self, nPrevHealth, nEffectCount):
            ''' Should we trigger a damage effect? '''
            nPrevRange = int( (nPrevHealth / float(self.maxhealth)) * nEffectCount )
            nRange = int( (self.health / float(self.maxhealth)) * nEffectCount )
            return ( nRange != nPrevRange )
        
        def CreateCorpse(self):
            ''' Character killed (only fired once) '''
            self.lifestate = LIFE_DEAD

            vecNormalizedMins = Vector(); vecNormalizedMaxs = Vector()
            vecAbsMins = Vector(); vecAbsMaxs = Vector()
            self.CollisionProp().WorldSpaceAABB(vecAbsMins, vecAbsMaxs)
            self.CollisionProp().WorldToNormalizedSpace(vecAbsMins, vecNormalizedMins)
            self.CollisionProp().WorldToNormalizedSpace(vecAbsMaxs, vecNormalizedMaxs)

            # Explode
            vecAbsPoint = Vector() 
            filter = CPASFilter(self.GetAbsOrigin())
            self.CollisionProp().RandomPointInBounds( vecNormalizedMins, vecNormalizedMaxs, vecAbsPoint)
            te.Explosion( filter, 0.0, vecAbsPoint, self.indexfireball, 
                random.randint( 4, 10 ), random.randint( 8, 15 ), TE_EXPLFLAG_NOPARTICLES, 100, 0 )

            # Break into chunks
            angVelocity = Vector()
            QAngleToAngularImpulse(self.GetLocalAngularVelocity(), angVelocity)
            PropBreakableCreateAll(self.GetModelIndex(), self.VPhysicsGetObject(), self.GetAbsOrigin(), self.GetAbsAngles(), self.GetAbsVelocity(), angVelocity, 1.0, 250, COLLISION_GROUP_NPC, self)

            # Create flaming gibs
            iChunks = random.randint( 4, 6 )
            for i in range(0, iChunks):
                self.ThrowFlamingGib()

            self.AddSolidFlags(FSOLID_NOT_SOLID)
            self.AddEffects(EF_NODRAW)
            UTIL_Remove(self)

        def ThrowFlamingGib(self):
            ''' Character killed (only fired once) '''
            vecAbsMins = Vector(); vecAbsMaxs = Vector()
            self.CollisionProp().WorldSpaceAABB(vecAbsMins, vecAbsMaxs)

            vecNormalizedMins = Vector(); vecNormalizedMaxs = Vector()
            self.CollisionProp().WorldToNormalizedSpace(vecAbsMins, vecNormalizedMins)
            self.CollisionProp().WorldToNormalizedSpace(vecAbsMaxs, vecNormalizedMaxs)

            vecAbsPoint = Vector()
            filter = CPASFilter(self.GetAbsOrigin())
            self.CollisionProp().RandomPointInBounds(vecNormalizedMins, vecNormalizedMaxs, vecAbsPoint)

            # Throw a flaming, smoking chunk.
            pChunk = CreateEntityByName( "gib" )
            pChunk.Spawn( "models/gibs/hgibs.mdl" )
            pChunk.SetBloodColor( DONT_BLEED )

            vecSpawnAngles = QAngle()
            vecSpawnAngles.Random( -90, 90 )
            pChunk.SetAbsOrigin( vecAbsPoint )
            pChunk.SetAbsAngles( vecSpawnAngles )

            nGib = random.randint(0, len(self.chunkmodelnames)-1)
            pChunk.Spawn(self.chunkmodelnames[nGib], random.uniform(6.0, 8.0))
            pChunk.SetOwnerEntity( self )
            pChunk.SetCollisionGroup( COLLISION_GROUP_DEBRIS )
            pPhysicsObject = pChunk.VPhysicsInitNormal( SOLID_VPHYSICS, pChunk.GetSolidFlags(), False )
            
            # Set the velocity
            if pPhysicsObject:
                pPhysicsObject.EnableMotion( True )
                vecVelocity = Vector()

                angles = QAngle()
                angles.x = random.uniform( -20, 20 )
                angles.y = random.uniform( 0, 360 )
                angles.z = 0.0
                AngleVectors( angles, vecVelocity )
                
                vecVelocity *= random.uniform( 300, 900 )
                vecVelocity += self.GetAbsVelocity()

                angImpulse = AngularImpulse()
                angImpulse = RandomAngularImpulse( -180, 180 )

                pChunk.SetAbsVelocity( vecVelocity )
                pPhysicsObject.SetVelocity(vecVelocity, angImpulse)

            pFlame = CEntityFlame.Create( pChunk, False )
            if pFlame != None:
                pFlame.SetLifetime( pChunk.lifetime )

            pSmokeTrail =  SmokeTrail.CreateSmokeTrail()
            if pSmokeTrail:
                pSmokeTrail.spawnrate = 80
                pSmokeTrail.particlelifetime = 0.8
                pSmokeTrail.startcolor = Vector(0.3, 0.3, 0.3)
                pSmokeTrail.endcolor = Vector(0.5, 0.5, 0.5)
                pSmokeTrail.startsize = 10
                pSmokeTrail.endsize = 40
                pSmokeTrail.spawnradius = 5
                pSmokeTrail.opacity = 0.4
                pSmokeTrail.minspeed = 15
                pSmokeTrail.maxspeed = 25
                pSmokeTrail.SetLifetime( pChunk.lifetime )
                pSmokeTrail.SetParent( pChunk, 0 )
                pSmokeTrail.SetLocalOrigin( vec3_origin )
                pSmokeTrail.SetMoveType( MOVETYPE_NONE )

        def Event_Killed(self, info):
            ''' Character killed (only fired once) '''
            if self.GetOwnerEntity():
                self.GetOwnerEntity().DropSoldierContainer()

            self.CreateCorpse()

        def OnTakeDamage(self, info):
            ''' Damage effects '''
            if self.health == 0:
                return 0

            # Airboat guns + explosive damage is all that can hurt it
            if ( info.GetDamageType() & (DMG_BLAST | DMG_AIRBOAT) ) == 0:
                return 0

            dmgInfo = info

            nPrevHealth = self.health

            if info.GetDamageType() & DMG_BLAST:
                # This check is necessary to prevent double-counting of rocket damage
                # from the blast hitting both the dropship + the container
                if (info.GetInflictor() != self.lastinflictor) or (gpGlobals.curtime != self.lasthittime):
                    self.health -= int(self.maxhealth / self.DROPSHIP_CRATE_ROCKET_HITS) + 1
                    self.lastinflictor = info.GetInflictor()
                    self.lasthittime = gpGlobals.curtime 
            else:
                self.health -= int(dmgInfo.GetDamage())

            if self.health <= 0:
                self.health = 0
                self.Event_Killed( dmgInfo )
                return 0

            # Spawn damage effects
            if nPrevHealth != self.health:
                if self.ShouldTriggerDamageEffect( nPrevHealth, self.MAX_SMOKE_TRAILS ):
                    self.AddSmokeTrail( dmgInfo.GetDamagePosition() )

                if self.ShouldTriggerDamageEffect( nPrevHealth, self.MAX_EXPLOSIONS ):
                    ExplosionCreate( dmgInfo.GetDamagePosition(), vec3_angle, self, 1000, 192,
                    SF_ENVEXPLOSION_NODAMAGE | SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSMOKE, 0 )
                    UTIL_ScreenShake( dmgInfo.GetDamagePosition(), 25.0, 150.0, 1.0, 750.0, SHAKE_START )

                    self.ThrowFlamingGib()

            return 1

        def AddSmokeTrail(self, vecPos):
            ''' Add a smoke trail since we've taken more damage '''
            # Start this trail out with a bang!
            ExplosionCreate( vecPos, vec3_angle, self, 2000, 100, SF_ENVEXPLOSION_NODAMAGE |
                SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSMOKE, 0 )
            UTIL_ScreenShake( vecPos, 25.0, 150.0, 1.0, 750.0, SHAKE_START )

            if self.smoketrailcount == self.MAX_SMOKE_TRAILS:
                return

            pSmokeTrail = SmokeTrail.CreateSmokeTrail()
            if not pSmokeTrail:
                return

            # See if there's an attachment for this smoke trail
            nAttachment = self.LookupAttachment('damage%d' % (self.smoketrailcount))

            self.smoketrailcount += 1

            pSmokeTrail.spawnrate = 20
            pSmokeTrail.particlelifetime = 4.0
            pSmokeTrail.startcolor = Vector( 0.7, 0.7, 0.7 )
            pSmokeTrail.endcolor = Vector( 0.6, 0.6, 0.6 )
            pSmokeTrail.startsize = 15
            pSmokeTrail.endsize = 50
            pSmokeTrail.spawnradius = 15
            pSmokeTrail.opacity = 0.75
            pSmokeTrail.minspeed = 10
            pSmokeTrail.maxspeed = 20
            pSmokeTrail.mindirectedspeed = 100.0
            pSmokeTrail.maxdirectedspeed = 120.0
            pSmokeTrail.SetLifetime( 5 )
            pSmokeTrail.SetParent(self, nAttachment)
            if nAttachment == 0:
                pSmokeTrail.SetAbsOrigin(vecPos)
            else:
                pSmokeTrail.SetLocalOrigin(vec3_origin)

            vecForward = Vector( -1, 0, 0 )
            angles = QAngle()
            VectorAngles( vecForward, angles )
            pSmokeTrail.SetAbsAngles( angles )
            pSmokeTrail.SetMoveType( MOVETYPE_NONE )

        def Remove(self):

            UTIL_Remove(self)

        lifetime = FloatField(value=0)
        smoketrailcount = 0
        lastinflictor = None
        lasthittime = 0
        
        DROPSHIP_CONTAINER_MODEL = "models/combine_dropship_container.mdl"
        MAX_SMOKE_TRAILS = 4
        MAX_EXPLOSIONS = 4
        DROPSHIP_CRATE_ROCKET_HITS = 4
        
        chunkmodelnames = [
            "models/gibs/helicopter_brokenpiece_01.mdl",
            "models/gibs/helicopter_brokenpiece_02.mdl",
            "models/gibs/helicopter_brokenpiece_03.mdl",
        ]
        gibmodelnames = [
            "models/combine_dropship_container.mdl",
        ]

class UnitBaseDropshipAnimState(UnitBaseHelicopterAnimState):
    def __init__(self, outer, *args, **kwargs):
        super().__init__(outer)
        
        self.anggun = QAngle(0,0,0)
        
    def SetActivityMap(self, *args, **kwargs): pass
    
    def OnNewModel(self):
        outer = self.outer
        studiohdr = outer.GetModelPtr()
 
        self.posecargobodyaccel = outer.LookupPoseParameter('cargo_body_accel')
        self.posecargobodysway = outer.LookupPoseParameter('cargo_body_sway')
        self.posebodyaccel = outer.LookupPoseParameter('body_accel')
        self.posebodysway = outer.LookupPoseParameter('body_sway')
        
        outer.SetPoseParameter(self.posecargobodyaccel, 0)
        outer.SetPoseParameter(self.posecargobodysway, 0)
        outer.SetPoseParameter(self.posebodyaccel, 0)
        outer.SetPoseParameter(self.posebodysway, 0)
        
    def Update(self, eyeyaw, eyepitch):
        super().Update(eyeyaw, eyepitch)
    
        outer = self.outer
        enemy = outer.enemy
        
        # GetAnimTimeInterval returns gpGlobals.frametime on client, and interval between main think (non context) on server
        interval = self.GetAnimTimeInterval()
        
        outer.SetSequence(outer.LookupSequence('cargo_idle'))

@entity('unit_combinedropship', networked=True)
class UnitCombineDropship(BaseClass):    
    """ Combine Dropship """
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 4048.0
        self.testroutestartheight = 1024.0
        
    AnimStateClass = UnitBaseDropshipAnimState
        
    if isserver:
        def Precache(self):
            super().Precache()
            
            self.PrecacheScriptSound( "NPC_CombineDropship.RotorLoop" )
            self.PrecacheScriptSound( "NPC_CombineDropship.FireLoop" )
            self.PrecacheScriptSound( "NPC_CombineDropship.NearRotorLoop" )
            self.PrecacheScriptSound( "NPC_CombineDropship.OnGroundRotorLoop" )
            self.PrecacheScriptSound( "NPC_CombineDropship.DescendingWarningLoop" )
            self.PrecacheScriptSound( "NPC_CombineDropship.NearRotorLoop" )
            self.PrecacheScriptSound( "combine_call_dropships" )
            
            UTIL_PrecacheOther("prop_dropship_container")
            
    def Spawn(self):
        super().Spawn()

        self.locomotion.desiredheight = 600.0
        #self.ammotype = GetAmmoDef().Index("CombineCannon")
        
        if isclient:
            self.InitializeRotorSound()
        else:
            self.CreateSoldierCrate()

        if self.lifetime != 0:
            self.SetThink(self.Remove, gpGlobals.curtime + self.lifetime, 'SelfDestructThink')

    def CreateComponents(self):
        super().CreateComponents()

        self.locomotion.no_unstuck = True

    def CreateSoldierCrate(self):
        self.container = CreateEntityByName("prop_dropship_container")
        if self.container:
            self.container.SetName("dropship_container")
            self.container.SetAbsOrigin(self.GetAbsOrigin())
            self.container.SetAbsAngles(self.GetAbsAngles())
            self.container.SetParent(self, 0)
            self.container.SetOwnerEntity(self)
            self.container.SetOwnerNumber(self.GetOwnerNumber())
            self.container.SetCollisionGroup(self.GetCollisionGroup())
            self.container.Spawn()

            physobj = self.container.VPhysicsGetObject()
            if physobj:
                physobj.SetShadow(1e4, 1e4, False, False)
                physobj.UpdateShadow(self.container.GetAbsOrigin(), self.container.GetAbsAngles(), False, 0)
                
            self.container.SetMoveType(MOVETYPE_PUSH)
            self.container.SetGroundEntity(None)

            # Cache off container's attachment points
            self.attachmenttroopdeploy = self.container.LookupAttachment( "deploy_landpoint" )
            self.attachmentdeploystart = self.container.LookupAttachment( "Deploy_Start" )
            self.muzzleattachment = self.container.LookupAttachment( "muzzle" )
            self.machinegunbaseattachment = self.container.LookupAttachment( "gun_base" )
            # NOTE: gun_ref must have the same position as gun_base, but rotates with the gun
            self.machinegunrefattachment = self.container.LookupAttachment( "gun_ref" )
            
    def DropSoldierContainer(self):
        ''' Drop the soldier container '''
        if not self.container:
            return
            
        self.container.SetParent(None, 0)
    #	self.container.SetOwnerEntity(None)

        vecAbsVelocity = self.GetAbsVelocity()
        if vecAbsVelocity.z > 0:
            vecAbsVelocity.z = 0.0

        self.container.SetAbsVelocity(vecAbsVelocity)
        self.container.SetMoveType(MOVETYPE_VPHYSICS)

        # If we have a troop in the process of exiting, kill him.
        # We do this to avoid having to solve the AI problems resulting from it.
        if self.lasttrooptoleave:
            dmgInfo = CTakeDamageInfo(self, self, vec3_origin, self.container.GetAbsOrigin(), self.lasttrooptoleave.maxhealth, DMG_GENERIC)
            self.lasttrooptoleave.TakeDamage(dmgInfo)

        # If the container has a physics object, remove it's shadow
        physobj = self.container.VPhysicsGetObject()
        if physobj:
            physobj.RemoveShadowController()
            physobj.SetVelocity(vecAbsVelocity, vec3_origin)

        UTIL_SetSize(self, self.DROPSHIP_BBOX_MIN, self.DROPSHIP_BBOX_MAX)

        self.container = None
        #SetLandingState( LANDING_NO )
        self.landtarget = None

        # TODO
        '''if m_bHasDroppedOff:
            m_OnContainerShotDownAfterDropoff.FireOutput( this, this )
        else:
            iTroopsNotUnloaded = (m_soldiersToDrop - m_iCurrentTroopExiting)
            if g_debug_dropship.GetInt():
                print("Dropship died, troops not unloaded: %d\n" % iTroopsNotUnloaded)

            m_OnContainerShotDownBeforeDropoff.Set(iTroopsNotUnloaded, self, self)'''
        
    def InitializeRotorSound(self):
        controller = CSoundEnvelopeController.GetController()

        filter = CPASAttenuationFilter(self)
        self.rotorsound = controller.SoundCreate(filter, self.entindex(), "NPC_CombineDropship.RotorLoop")
        self.nearrotorsound = controller.SoundCreate(filter, self.entindex(), "NPC_CombineDropship.NearRotorLoop")
        self.rotorongroundsound = controller.SoundCreate(filter, self.entindex(), "NPC_CombineDropship.OnGroundRotorLoop")
        self.descendingwarningsound = controller.SoundCreate(filter, self.entindex(), "NPC_CombineDropship.DescendingWarningLoop")
        self.cannonsound = controller.SoundCreate(filter, self.entindex(), "NPC_CombineDropship.FireLoop")

        # NOTE: self.rotorsound is started up by the base class
        if self.cannonsound:
            controller.Play( self.cannonsound, 0.0, 100 )

        if self.descendingwarningsound:
            controller.Play( self.descendingwarningsound, 0.0, 100 )

        if self.rotorongroundsound:
            controller.Play( self.rotorongroundsound, 0.0, 100 )
        
        if self.nearrotorsound:
            controller.Play( self.nearrotorsound, 0.0, 100 )

        self.enginethrust = 1.0

        super().InitializeRotorSound()

    def SummonDropship(self, inputdata=None):
        """ Fires the canister! """
        if self.summoned:
            return

        self.summoned = True
        self.EmitSound( "combine_call_dropships" )

    def StopLoopingSounds(self):
        controller = CSoundEnvelopeController.GetController()

        if self.cannonsound:
            controller.SoundDestroy( self.cannonsound )
            self.cannonsound = None

        if self.rotorongroundsound:
            controller.SoundDestroy( self.rotorongroundsound )
            self.rotorongroundsound = None

        if self.descendingwarningsound:
            controller.SoundDestroy( self.descendingwarningsound )
            self.descendingwarningsound = None

        if self.nearrotorsound:
            controller.SoundDestroy( self.nearrotorsound )
            self.nearrotorsound = None

        self.summoned = False

        super().StopLoopingSounds()

    def UpdateRotorWashVolumeDropship(self, pRotorSound, flVolume, flDeltaTime):
        ''' Updates the rotor wash volume '''
        if not pRotorSound:
            return

        controller = CSoundEnvelopeController.GetController()
        flVolDelta = flVolume - controller.SoundGetVolume( pRotorSound )
        if flVolDelta:
            # We can change from 0 to 1 in 3 seconds. 
            # Figure out how many seconds flVolDelta will take.
            flRampTime = abs( flVolDelta ) * flDeltaTime 
            controller.SoundChangeVolume( pRotorSound, flVolume, flRampTime )
        
    def UpdateRotorWashVolume(self):
        ''' Updates the rotor wash volume '''
        flNearFactor = 0.0
        player = CBasePlayer.GetLocalPlayer()
        if player:
            flDist = player.GetAbsOrigin().DistTo(self.GetAbsOrigin())
            flDist = clamp( flDist, self.DROPSHIP_NEAR_SOUND_MIN_DISTANCE, self.DROPSHIP_NEAR_SOUND_MAX_DISTANCE )
            flNearFactor = RemapVal(flDist, self.DROPSHIP_NEAR_SOUND_MIN_DISTANCE, self.DROPSHIP_NEAR_SOUND_MAX_DISTANCE, 1.0, 0.0)

        if self.rotorsound:
            self.UpdateRotorWashVolumeDropship(self.rotorsound, self.enginethrust * self.GetRotorVolume() * (1.0 - flNearFactor), 3.0)

        if self.nearrotorsound:
            self.UpdateRotorWashVolumeDropship(self.nearrotorsound, self.enginethrust * self.GetRotorVolume() * flNearFactor, 3.0)
        
    def UpdateRotorSoundPitch(self, iPitch):
        controller = CSoundEnvelopeController.GetController()

        rotorPitch = 0.2 + self.enginethrust * 0.8
        if self.rotorsound:
            controller.SoundChangePitch(self.rotorsound, iPitch + rotorPitch, 0.1)

        if self.nearrotorsound:
            controller.SoundChangePitch(self.nearrotorsound, iPitch + rotorPitch, 0.1)

        if self.rotorongroundsound:
            controller.SoundChangePitch(self.rotorongroundsound, iPitch + rotorPitch, 0.1)

        self.UpdateRotorWashVolume()
        
    def OnChangeOwnerNumber(self, oldownernumber):
        super().OnChangeOwnerNumber(oldownernumber)
        
        if self.container:
            self.container.SetOwnerNumber(self.GetOwnerNumber())
            self.container.SetCollisionGroup(self.GetCollisionGroup())
            
    def DeploySoldiers(self):
        ''' Test method for releasing soldiers. '''
        deploypos = Vector()
        deployangle = QAngle()
        if self.attachmenttroopdeploy != -1:
            self.container.GetAttachment(self.attachmenttroopdeploy, deploypos, deployangle)
            deployangle.x = deployangle.z = 0
        else:
            deploypos = self.GetAbsOrigin()
            deployangle = QAngle(0, self.GetAbsAngles().y, 0)
        
        for i in range(0, 5):
            CreateUnitFancy('unit_combine', deploypos, angles=deployangle, owner_number=self.GetOwnerNumber())

    def Remove(self):

        UTIL_Remove(self)

    lifetime = FloatField(value=0)
    enginethrust = 1.0
    summoned = False
    
    cannonsound = None
    rotorongroundsound = None
    descendingwarningsound = None
    nearrotorsound = None
    
    container = None
    lasttrooptoleave = None
    
    attachmenttroopdeploy = -1
    attachmentdeploystart = -1
    muzzleattachment = -1
    machinegunbaseattachment = -1
    machinegunrefattachment = -1
    
    DROPSHIP_NEAR_SOUND_MIN_DISTANCE = 1000
    DROPSHIP_NEAR_SOUND_MAX_DISTANCE = 2500
    DROPSHIP_GROUND_WASH_MIN_ALTITUDE = 100.0
    DROPSHIP_GROUND_WASH_MAX_ALTITUDE = 750.0
    
    # With crate
    DROPSHIP_BBOX_CRATE_MIN = -Vector(60,60,160)
    DROPSHIP_BBOX_CRATE_MAX = Vector(60,60,0)
    # Without crate
    DROPSHIP_BBOX_MIN = -Vector(40,40,0)
    DROPSHIP_BBOX_MAX = Vector(40,40,40)
    # dropshipcount = UpgradeField(value=1, abilityname='dropsoldiers_upgrade_lvl3')

    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_DROPSHIP_FLY_IDLE',
        'ACT_DROPSHIP_FLY_IDLE_EXAGG',
        'ACT_DROPSHIP_FLY_IDLE_CARGO',
        'ACT_DROPSHIP_DESCEND_IDLE',
    ] )
        
class CombineDropshipInfo(UnitInfo):
    name = 'unit_combinedropship'
    cls_name = 'unit_combinedropship'
    displayname = '#CombDropship_Name'
    description = '#CombDropship_Description'
    #image_name = 'vgui/combine/units/unit_combinedropship'
    costs = [('requisition', 150), ('power', 180)]
    buildtime = 120.0
    zoffset = 128.0
    scale = 0.75
    modelname = 'models/combine_dropship.mdl'
    hulltype = 'HULL_LARGE_CENTERED'
    health = 800
    population = 0
    turnspeed = 10
    maxspeed = 450
    viewdistance = 0
    attributes = ['synth', 'pulse']
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }