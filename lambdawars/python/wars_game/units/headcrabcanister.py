from srcbase import *
from math import sqrt
from vmath import (Vector, QAngle, VectorMultiply, vec3_origin, vec3_angle, CrossProduct, VectorMA, VectorSubtract, VectorNormalize,
                   VMatrix, MatrixBuildRotationAboutAxis, MatrixMultiply, MatrixToAngles, MatrixFromAngles)
from core.units import UnitInfo, UnitBase as BaseClass
from entities import entity, ACT_INVALID, FOWFLAG_UPDATER
from fields import StringField, VectorField, QAngleField, BooleanField, IntegerField, FloatField, OutputField, FlagsField, input
import random
from utils import UTIL_EntitiesInSphere
from wars_game.statuseffects import StunnedEffectInfo
from _recast import RecastMgr

if isserver:
    from core.units import CreateUnitNoSpawn, PrecacheUnit
    from entities import SmokeTrail, CSpriteTrail, EFL_IN_SKYBOX, gEntList, GetCurrentSkyCamera, DispatchSpawn, variant_t
    from utils import (UTIL_TraceLine, trace_t, CTraceFilterWorldOnly, UTIL_ScreenShake, SHAKE_START, UTIL_PlayerByIndex, UTIL_Remove,
                       ExplosionCreate, SF_ENVEXPLOSION_NODLIGHTS, SF_ENVEXPLOSION_NOSPARKS, SF_ENVEXPLOSION_NODAMAGE, SF_ENVEXPLOSION_NOSOUND)
    from sound import ATTN_NONE
    from gameinterface import CPASAttenuationFilter
else:
    from entities import DATA_UPDATE_CREATED, CLIENT_THINK_ALWAYS, CLIENT_THINK_NEVER

@entity('unit_headcrabcanister', networked=True)
class UnitHeadcrabCanister(BaseClass):
    # Shared
    def InitInWorld(self, flLaunchTime, 
            vecStartPosition, vecStartAngles, 
            vecDirection, vecImpactPosition, bLaunchedFromWithinWorld=False):
        """ Creates a headcrab canister in the world """
        vecActualStartPosition = Vector(vecStartPosition)
        if not bLaunchedFromWithinWorld:
            # Move the start position inward if it's too close
            vecDelta = Vector()
            VectorSubtract(vecStartPosition, vecImpactPosition, vecDelta)
            VectorNormalize(vecDelta)

            VectorMA(vecImpactPosition, self.flighttime * self.flightspeed, vecDelta, vecActualStartPosition)

        # Setup initial parametric state.
        self.launchtime = flLaunchTime
        self.vecstartposition = vecActualStartPosition
        self.vecenterworldposition = vecActualStartPosition
        self.vecdirection = vecDirection
        self.vecstartangles = vecStartAngles
        self.worldentertime = 0.0
        self.inskybox = False
        self.launchedfromwithinworld = bLaunchedFromWithinWorld
     
        if self.launchedfromwithinworld:
            self.skyboxscale = 1
            self.vecskyboxorigin = Vector(vec3_origin)

            flLength = self.vecdirection.AsVector2D().Length()
            VectorSubtract(vecImpactPosition, vecStartPosition, self.vecparaboladirection)
            self.vecparaboladirection.z = 0
            self.vecparaboladirection = Vector(self.vecparaboladirection) # Temp, to trigger networked changed.
            flTotalDistance = VectorNormalize(self.vecparaboladirection)
            #self.vecdirection.x = flLength * self.vecparaboladirection.x
            #self.vecdirection.y = flLength * self.vecparaboladirection.y
            self.vecdirection = Vector(flLength * self.vecparaboladirection.x, 
                                       flLength * self.vecparaboladirection.y, 
                                       self.vecdirection.z)
     
            #self.horizspeed = flTotalDistance / self.flighttime
            self.flighttime = flTotalDistance / self.horizspeed 
            self.worldentertime = 0
     
            flFinalZSpeed = self.vecdirection.z * self.horizspeed
            self.flightspeed = sqrt( self.horizspeed * self.horizspeed + flFinalZSpeed * flFinalZSpeed )
            self.initialzspeed = (2.0 * ( vecImpactPosition.z - vecStartPosition.z ) - flFinalZSpeed * self.flighttime) / self.flighttime
            self.zacceleration = (flFinalZSpeed - self.initialzspeed) / self.flighttime

    def InitInSkybox(self, flLaunchTime, 
            vecStartPosition, vecStartAngles, vecDirection,
            vecImpactPosition, vecSkyboxOrigin, flSkyboxScale):
        """ Creates a headcrab canister in the skybox """
        # Compute a horizontal speed (constant)
        self.vecparaboladirection = Vector(vecDirection.x, vecDirection.y, 0.0)
        flLength = VectorNormalize( self.vecparaboladirection ) 
        self.horizspeed = flLength * self.flightspeed

        # compute total distance to travel
        flTotalDistance = self.flighttime * self.horizspeed
        flTotalDistance -= vecStartPosition.AsVector2D().DistTo( vecImpactPosition.AsVector2D() )
        if flTotalDistance <= 0.0:
            self.InitInWorld( flLaunchTime, vecStartPosition, vecStartAngles, vecDirection, vecImpactPosition )
            return

        # Setup initial parametric state.
        self.launchtime = flLaunchTime
        self.worldentertime = flTotalDistance / self.horizspeed
        self.vecskyboxorigin = vecSkyboxOrigin
        self.skyboxscale = flSkyboxScale

        self.vecenterworldposition = vecStartPosition
        self.vecdirection = vecDirection
        self.vecstartangles = vecStartAngles
        self.inskybox = True
        self.launchedfromwithinworld = False

        # Compute parabolic course
        # Assume the x velocity remains constant.
        # Z moves ballistically, as if under gravity
        # zf + lh = zo
        # vf = vo + a*t
        # zf = zo + vo*t + 0.5 * a * t*t
        # a*t = vf - vo
        # zf = zo + vo*t + 0.5f * (vf - vo) * t
        # zf - zo = 0.5f *vo*t + 0.5f * vf * t
        # -lh - 0.5f * vf * t = 0.5f * vo * t
        # vo = -2.0f * lh / t - vf
        # a = (vf - vo) / t
        self.horizspeed /= flSkyboxScale

        VectorMA( vecSkyboxOrigin, 1.0 / self.skyboxscale, vecStartPosition, self.vecstartposition )
        VectorMA( self.vecstartposition, -self.horizspeed * self.worldentertime, self.vecparaboladirection, self.vecstartposition )

        flLaunchHeight = self.launchheight / flSkyboxScale
        flFinalZSpeed = self.vecdirection.z * self.flightspeed / flSkyboxScale
        self.vecstartposition.z += flLaunchHeight
        self.zacceleration = 2.0 * ( flLaunchHeight + flFinalZSpeed * self.worldentertime ) / ( self.worldentertime * self.worldentertime )
        self.initialzspeed = flFinalZSpeed - self.zacceleration * self.worldentertime

    def ConvertFromSkyboxToWorld(self):
        """ Convert from skybox to world """
        assert( self.inskybox )
        self.inskybox = False

    def GetEnterWorldTime(self):
        """ Returns the time at which it enters the world """
        return self.worldentertime

    def DidImpact(self, flTime):
        """ Did we impact? """
        return (flTime - self.launchtime) >= self.flighttime

    def GetPositionAtTime(self, flTime, vecPosition, vecAngles):
        """ Computes the position of the canister """
        flDeltaTime = flTime - self.launchtime
        if flDeltaTime > self.flighttime:
            flDeltaTime = self.flighttime
            
        initToWorld = VMatrix()
        initToWorld.Identity()
        if self.launchedfromwithinworld or self.inskybox:
            VectorMA( self.vecstartposition, flDeltaTime * self.horizspeed, self.vecparaboladirection, vecPosition )
            vecPosition.z += self.initialzspeed * flDeltaTime + 0.5 * self.zacceleration * flDeltaTime * flDeltaTime

            vecLeft = Vector()
            CrossProduct( self.vecparaboladirection, Vector( 0, 0, 1 ), vecLeft )

            vecForward = Vector()
            VectorMultiply( self.vecparaboladirection, -1.0, vecForward )
            vecForward.z = -(self.initialzspeed + self.zacceleration * flDeltaTime) / self.horizspeed	# This is -dz/dx.
            VectorNormalize( vecForward )

            vecUp = Vector()
            CrossProduct(vecForward, vecLeft, vecUp)
     
            initToWorld.SetBasisVectors(vecForward, vecLeft, vecUp)
        else:
            flDeltaTime -= self.worldentertime
            vecVelocity = Vector()
            VectorMultiply(self.vecdirection, self.flightspeed, vecVelocity)
            VectorMA(self.vecenterworldposition, flDeltaTime, vecVelocity, vecPosition)

            MatrixFromAngles(self.vecstartangles, initToWorld)

        rotation = VMatrix()
        MatrixBuildRotationAboutAxis(rotation, Vector( 1, 0, 0 ), flDeltaTime * self.ROTATION_SPEED)

        newAngles = VMatrix()
        MatrixMultiply(initToWorld, rotation, newAngles)
        MatrixToAngles(newAngles, vecAngles)
        
        #if not vecAngles.IsValid():
        #    vecAngles.Init(0,0,0)

    def IsInSkybox(self):
        """ Are we in the skybox? """
        # Check to see if we are always in the world!
        return self.inskybox
        
    # Animations (shared)
    STATE_CLOSED = 0
    STATE_OPENING = 1
    STATE_OPEN = 2
    
    if isclient:
        oldstate = -1
        def OnDataChanged(self, updatetype):
            super().OnDataChanged(updatetype)
            
            if updatetype == DATA_UPDATE_CREATED:
                self.SetNextClientThink(CLIENT_THINK_ALWAYS)

            # Stop client-side simulation on landing
            if self.landed:
                self.SetNextClientThink(CLIENT_THINK_NEVER)
    
            # Deal with client side animations
            if self.oldstate != self.state:
                if self.state == self.STATE_CLOSED:
                    self.ResetSequence(self.LookupSequence('idle_closed'))
                elif self.state == self.STATE_OPENING:
                    self.ResetSequence(self.LookupSequence('open'))
                elif self.state == self.STATE_OPEN:
                    self.ResetSequence(self.LookupSequence('idle_open'))
                self.oldstate = self.state

        def ClientThink(self):
            """ Compute position """
            vecEndPosition = Vector()
            vecEndAngles = QAngle()
            self.GetPositionAtTime(gpGlobals.curtime, vecEndPosition, vecEndAngles)
            self.SetAbsOrigin(vecEndPosition)
            self.SetAbsAngles(vecEndAngles)
            
        def Spawn(self):
            super().Spawn()
            
            self.SetBloodColor(DONT_BLEED)

    # Server only
    if isserver:
        def Precache(self):
            super().Precache()
        
            self.PrecacheModel(self.ENV_HEADCRABCANISTER_MODEL)
            self.PrecacheModel(self.ENV_HEADCRABCANISTER_BROKEN_MODEL)
            self.PrecacheModel(self.ENV_HEADCRABCANISTER_SKYBOX_MODEL)
            self.PrecacheModel('sprites/smoke.vmt')

            self.PrecacheScriptSound('HeadcrabCanister.LaunchSound')
            self.PrecacheScriptSound('HeadcrabCanister.AfterLanding')
            self.PrecacheScriptSound('HeadcrabCanister.Explosion')
            self.PrecacheScriptSound('HeadcrabCanister.IncomingSound')
            self.PrecacheScriptSound('HeadcrabCanister.SkyboxExplosion')
            self.PrecacheScriptSound('HeadcrabCanister.Open')
            
            PrecacheUnit(self.headcrabclass[self.headcrabtype])
    
        def Spawn(self):
            super().Spawn()

            self.viewdistance = 320.0
            self.AddFlag(FL_AIMTARGET|FL_NPC) 
            self.lifestate = LIFE_ALIVE
            self.takedamage = DAMAGE_YES
            
            self.SetCanBeSeen(False)
            
            # Do we have a position to launch from?
            if self.launchpositionname:
                # It doesn't have any real presence at first.
                self.SetSolid(SOLID_NONE)

                self.vecimpactposition = self.GetAbsOrigin()
                self.incomingsoundstarted = False
                self.landed = False
                self.hasdetonated = False
                self.opened = False
            elif not self.HasSpawnFlags(self.SF_START_IMPACTED):
                # It doesn't have any real presence at first.
                self.SetSolid(SOLID_NONE)

                if not self.HasSpawnFlags(self.SF_LAND_AT_INITIAL_POSITION):
                    vecForward = Vector()
                    self.GetVectors(vecForward, None, None)
                    vecForward *= -1.0

                    trace = trace_t()
                    UTIL_TraceLine(self.GetAbsOrigin(), self.GetAbsOrigin() + vecForward * 10000, MASK_NPCWORLDSTATIC, 
                        self, COLLISION_GROUP_NONE, trace)

                    self.vecimpactposition = trace.endpos
                else:
                    self.vecimpactposition = self.GetAbsOrigin()

                self.incomingsoundstarted = False
                self.landed = False
                self.hasdetonated = False
                self.opened = False
            else:
                self.hasdetonated = True
                self.incomingsoundstarted = True
                self.opened = False
                self.vecimpactposition = self.GetAbsOrigin()
                self.Landed()
                
            if self.lifetime != 0:
                self.SetThink(self.Remove, gpGlobals.curtime + self.lifetime, 'SelfDestructThink')
                
        def SetUnitModel(self, *args, **kwargs):
            pass # Don't set model in base class

        def UpdateOnRemove(self):
            """ On remove! """
            super().UpdateOnRemove()
            self.StopSound("HeadcrabCanister.AfterLanding")
            if self.trail:
                UTIL_Remove(self.trail)
                self.trail = None
            if self.smoketrail:
                UTIL_Remove(self.smoketrail)
                self.smoketrail = None

        def SetupWorldModel(self):
            """ Set up the world model """
            self.SetModel(self.ENV_HEADCRABCANISTER_MODEL)
            self.SetSolid(SOLID_BBOX)

            flRadius = self.CollisionProp().BoundingRadius()
            vecMins = Vector(-flRadius, -flRadius, -flRadius)
            vecMaxs = Vector(flRadius, flRadius, flRadius)
            self.SetSize(vecMins, vecMaxs)
            
        def ComputeWorldEntryPoint(self):
            """ Figure out where we enter the world """
            self.SetupWorldModel()

            vecForward = Vector()
            self.GetVectors(vecForward, None, None)

            # Raycast up to the place where we should start from (start raycast slightly off the ground,
            # since it'll be buried in the ground oftentimes)
            tr = trace_t()
            filter = CTraceFilterWorldOnly()
            UTIL_TraceLine(self.GetAbsOrigin() + vecForward * 100, self.GetAbsOrigin() + vecForward * 10000,
                CONTENTS_SOLID, filter, tr)

            startposition = Vector(tr.endpos)
            startangles = self.GetAbsAngles()
            startdirection = Vector()
            VectorMultiply(vecForward, -1.0, startdirection)
            return startposition, startangles, startdirection
            
        def PlaceCanisterInWorld(self):
            """ Place the canister in the world """
            pCamera = None

            # Are we launching from a point? If so, use that point.
            if self.launchpositionname:
                # Get the launch position entity
                pLaunchPos = gEntList.FindEntityByName(None, self.launchpositionname)
                if not pLaunchPos:
                    PrintWarning("%s (%s) could not find an entity matching LaunchPositionName of '%s'\n" % (self.GetEntityName(), self.GetDebugName(), self.launchpositionname))
                    self.SUB_Remove()
                else:
                    self.SetupWorldModel()

                    vecForward = Vector()
                    vecImpactDirection = Vector()
                    self.GetVectors(vecForward, None, None)
                    VectorMultiply(vecForward, -1.0, vecImpactDirection)

                    self.InitInWorld(gpGlobals.curtime, pLaunchPos.GetAbsOrigin(), self.GetAbsAngles(), 
                        vecImpactDirection, self.vecimpactposition, True)
                    self.SetThink(self.HeadcrabCanisterWorldThink)
                    self.SetNextThink(gpGlobals.curtime)
            elif self.DetectInSkybox():
                pCamera = self.GetEntitySkybox()

                self.SetModel(self.ENV_HEADCRABCANISTER_SKYBOX_MODEL)
                self.SetSolid(SOLID_NONE)

                vecForward = Vector()
                self.GetVectors(vecForward, None, None)
                vecForward *= -1.0

                self.InitInSkybox(gpGlobals.curtime, self.vecimpactposition, GetAbsAngles(), vecForward, 
                    self.vecimpactposition, pCamera.m_skyboxData.origin, pCamera.m_skyboxData.scale)
                self.AddEFlags(EFL_IN_SKYBOX)
                self.SetThink(self.HeadcrabCanisterSkyboxOnlyThink)
                self.SetNextThink(gpGlobals.curtime + self.GetEnterWorldTime() + gpGlobals.interval_per_tick)
            else:
                vecStartPosition, vecStartAngles, vecDirection = self.ComputeWorldEntryPoint() 

                # Figure out which skybox to place the entity in.
                pCamera = None #GetCurrentSkyCamera()
                if pCamera:
                    self.InitInSkybox(gpGlobals.curtime, vecStartPosition, vecStartAngles, vecDirection, 
                        self.vecimpactposition, pCamera.m_skyboxData.origin, pCamera.m_skyboxData.scale)

                    if self.IsInSkybox():
                        self.SetModel(self.ENV_HEADCRABCANISTER_SKYBOX_MODEL)
                        self.SetSolid(SOLID_NONE)
                        self.AddEFlags(EFL_IN_SKYBOX)
                        self.SetThink(self.HeadcrabCanisterSkyboxThink)
                        self.SetNextThink(gpGlobals.curtime + self.GetEnterWorldTime())
                    else:
                        self.SetThink(self.HeadcrabCanisterWorldThink)
                        self.SetNextThink(gpGlobals.curtime)
                else:
                    self.InitInWorld(gpGlobals.curtime, vecStartPosition, vecStartAngles, 
                        vecDirection, self.vecimpactposition)
                    self.SetThink(self.HeadcrabCanisterWorldThink)
                    self.SetNextThink(gpGlobals.curtime)

            vecEndPosition = Vector()
            vecEndAngles = QAngle(0,0,0)
            self.GetPositionAtTime(gpGlobals.curtime, vecEndPosition, vecEndAngles)
            self.SetAbsOrigin(vecEndPosition)
            self.SetAbsAngles(vecEndAngles)

            return pCamera
            
        @input(inputname='FireCanister')
        def InputFireCanister(self, inputdata=None):
            """ Fires the canister! """
            if self.launched:
                return

            self.launched = True

            if self.HasSpawnFlags(self.SF_START_IMPACTED):
                StartSpawningHeadcrabs(0.01)
                return

            # Play a firing sound
            filter = CPASAttenuationFilter(self, ATTN_NONE)

            if not self.HasSpawnFlags(self.SF_NO_LAUNCH_SOUND):
                self.EmitSoundFilter( filter, self.entindex(), "HeadcrabCanister.LaunchSound" )

            # Place the canister
            pCamera = self.PlaceCanisterInWorld()

            # Hook up a smoke trail
            self.trail = CSpriteTrail.SpriteTrailCreate("sprites/smoke.vmt", self.GetAbsOrigin(), True)
            self.trail.SetTransparency(kRenderTransAdd, 224, 224, 255, 255, kRenderFxNone)
            self.trail.SetAttachment(self, 0)
            self.trail.SetStartWidth(32.0)
            self.trail.SetEndWidth(200.0)
            self.trail.SetStartWidthVariance(15.0)
            self.trail.SetTextureResolution(0.002)
            self.trail.SetLifeTime(self.ENV_HEADCRABCANISTER_TRAIL_TIME)
            self.trail.SetMinFadeLength(1000.0)

            if pCamera and self.IsInSkybox():
                self.trail.SetSkybox( pCamera.m_skyboxData.origin, pCamera.m_skyboxData.scale )

            # Fire that output!
            var = variant_t()
            var.SetEntity(self)
            self.onlaunched.Set(var)
            self.onlaunched.FireOutput(self, self)
            
        @input(inputname='OpenCanister')
        def InputOpenCanister(self, inputdata=None):
            """ Opens the canister!"""
            if self.landed and not self.opened and self.HasSpawnFlags(self.SF_WAIT_FOR_INPUT_TO_OPEN):
                self.OpenCanister()

        @input(inputname='SpawnHeadcrabs')
        def InputSpawnHeadcrabs(self, inputdata=None):
            """ Spawns headcrabs """
            if self.landed and self.opened and self.HasSpawnFlags(self.SF_WAIT_FOR_INPUT_TO_SPAWN_HEADCRABS):
                self.StartSpawningHeadcrabs(0.01)

        @input(inputname='StopSmoke')
        def InputStopSmoke(self, inputdata=None):
            if self.smoketrail != None:
                UTIL_Remove(self.smoketrail)
                self.smoketrail = None
            
        def HeadcrabCanisterSpawnHeadcrabThink(self):
            """ Headcrab creation """
            if not self.IsAlive():
                return
            
            vecSpawnPosition = Vector()
            vecSpawnAngles = QAngle()

            self.headcrabcount -= 1

            nHeadCrabAttachment = self.LookupAttachment( "headcrab" )
            if self.GetAttachment(nHeadCrabAttachment, vecSpawnPosition, vecSpawnAngles):
                headcrab = CreateUnitNoSpawn(self.headcrabclass[self.headcrabtype], owner_number=self.GetOwnerNumber())
                headcrab.launcher_owner = self.launcher_owner

                # Necessary to get it to eject properly (don't allow the NPC
                # to override the spawn position specified).
                #headcrab.AddSpawnFlags(SF_NPC_FALL_TO_GROUND)

                # So we don't collide with the canister
                # NOTE: Hierarchical attachment is necessary here to get the animations to work
                headcrab.SetOwnerEntity(self)
                if self.fnprespawnheadcrab:
                    self.fnprespawnheadcrab(headcrab)
                DispatchSpawn(headcrab)
                if self.fnpostspawnheadcrab:
                    self.fnpostspawnheadcrab(headcrab)
                headcrab.CrawlFromCanister()
                headcrab.SetParent(self, nHeadCrabAttachment)
                headcrab.SetLocalOrigin(vec3_origin)
                headcrab.SetLocalAngles(vec3_angle)
                headcrab.uncontrollable = True
                
            if self.headcrabcount != 0:
                flWaitTime = random.uniform(0.4, 0.8)
                self.SetThink(self.HeadcrabCanisterSpawnHeadcrabThink, gpGlobals.curtime + flWaitTime, 'HeadcrabThink')
            else:
                self.SetThink(None, gpGlobals.curtime, 'HeadcrabThink')

        def StartSpawningHeadcrabs(self, flDelay):
            """ Start spawning headcrabs """
            if not self.landed or not self.opened or self.headcrabcount == 0:
                return

            if self.headcrabcount != 0:
                self.SetThink(self.HeadcrabCanisterSpawnHeadcrabThink, gpGlobals.curtime + flDelay, 'HeadcrabThink')

        def CanisterFinishedOpening(self):
            """ Canister finished opening """
            self.ResetSequence(self.LookupSequence( "idle_open" ))
            self.state = self.STATE_OPEN
            self.onopened.FireOutput(self, self, 0)
            self.opened = True
            self.SetThink(None, gpGlobals.curtime, 'OpenThink')

            if not self.HasSpawnFlags(self.SF_START_IMPACTED):
                if not self.HasSpawnFlags(self.SF_WAIT_FOR_INPUT_TO_SPAWN_HEADCRABS):
                    self.StartSpawningHeadcrabs(2.0)

        def WaitForOpenSequenceThink(self):
            """ Finish the opening sequence """
            self.StudioFrameAdvance()
            if self.GetSequence() == self.LookupSequence( "open" ) and self.IsSequenceFinished():
                self.CanisterFinishedOpening()
            else:
                self.SetThink(self.WaitForOpenSequenceThink, gpGlobals.curtime + 0.01, 'OpenThink')


        def OpenCanister(self):
            """ Open the canister! """
            if self.opened:
                return

            nOpenSequence = self.LookupSequence( "open" )
            if nOpenSequence != ACT_INVALID:
                self.EmitSound( "HeadcrabCanister.Open" )

                self.ResetSequence( nOpenSequence )
                self.state = self.STATE_OPENING
                self.SetThink(self.WaitForOpenSequenceThink, gpGlobals.curtime + 0.01, 'OpenThink')
            else:
                self.CanisterFinishedOpening()

        def SetLanded(self):
            self.SetAbsOrigin(self.vecimpactposition)
            self.SetModel(self.ENV_HEADCRABCANISTER_BROKEN_MODEL)
            self.SetMoveType(MOVETYPE_NONE)
            self.SetSolid(SOLID_VPHYSICS)
            self.VPhysicsInitStatic()
            
            self.AddEffects(EF_NOINTERP)
            self.landed = True
            
        def Landed(self):
            """ Landed! """
            self.EmitSound("HeadcrabCanister.AfterLanding")
            
            self.SetCanBeSeen(True)

            # Lock us now that we've stopped
            self.SetLanded()

            # Hook the follow trail to the lead of the canister (which should be buried)
            # to hide problems with the edge of the follow trail
            if self.trail:
                self.trail.SetAttachment(self, self.LookupAttachment("trail"))

            # Start smoke, unless we don't want it
            if not self.HasSpawnFlags(self.SF_NO_SMOKE):
                # Create the smoke trail to obscure the headcrabs
                self.smoketrail = SmokeTrail.CreateSmokeTrail()
                self.smoketrail.FollowEntity(self, "smoke")

                self.smoketrail.spawnrate = 8
                self.smoketrail.particlelifetime = 2.0

                self.smoketrail.startcolor = Vector( 0.7, 0.7, 0.7 )
                self.smoketrail.endcolor = Vector( 0.6, 0.6, 0.6 )

                self.smoketrail.startsize	= 32
                self.smoketrail.endsize	= 64
                self.smoketrail.spawnradius= 8
                self.smoketrail.minspeed	= 0
                self.smoketrail.maxspeed	= 8
                self.smoketrail.mindirectedspeed	= 32
                self.smoketrail.maxdirectedspeed	= 64
                self.smoketrail.opacity	= 0.35

                self.smoketrail.SetLifetime(self.smokelifetime)

            self.SetThink(None)
            
            RecastMgr().AddEntRadiusObstacle(self, self.CollisionProp().BoundingRadius2D(), self.CollisionProp().OBBSize().z)

            if not self.HasSpawnFlags(self.SF_WAIT_FOR_INPUT_TO_OPEN):
                if self.HasSpawnFlags(self.SF_START_IMPACTED):
                    self.CanisterFinishedOpening()
                else:
                    self.OpenCanister()
                    
        def Event_Killed(self, info):
            self.lifestate = LIFE_DYING
            
            self.Detonate(True)
        
        def Detonate(self, forceremove=False):
            """ Creates the explosion effect """
            # Send the impact output
            self.onimpacted.FireOutput(self, self, 0)

            if not self.HasSpawnFlags(self.SF_NO_IMPACT_SOUND):
                self.StopSound("HeadcrabCanister.IncomingSound")
                self.EmitSound("HeadcrabCanister.Explosion")

            # If we're supposed to be removed, do that now
            if forceremove or self.HasSpawnFlags(self.SF_REMOVE_ON_IMPACT):
                self.SetAbsOrigin(self.vecimpactposition)
                self.SetModel(self.ENV_HEADCRABCANISTER_BROKEN_MODEL)
                self.SetMoveType(MOVETYPE_NONE)
                self.AddEffects(EF_NOINTERP)
                self.landed = True
                
                # Become invisible so our trail can finish up
                self.AddEffects(EF_NODRAW)
                self.SetSolidFlags(FSOLID_NOT_SOLID)

                self.SetThink(self.SUB_Remove)
                self.SetNextThink(gpGlobals.curtime + self.ENV_HEADCRABCANISTER_TRAIL_TIME)

                return

            # Test for damaging things
            # TODO
            #self.TestForCollisionsAgainstWorld(self.vecimpactposition)

            # Shake the screen unless flagged otherwise
            if not self.HasSpawnFlags(self.SF_NO_SHAKE):
                pPlayer = UTIL_PlayerByIndex(1)

                # If the player is on foot, then do a more limited shake
                shakeRadius = self.ENV_HEADCRABCANISTER_SHAKE_RADIUS_VEHICLE if (pPlayer and pPlayer.IsInAVehicle()) else self.ENV_HEADCRABCANISTER_SHAKE_RADIUS
                shakeRadius = 512.0

                UTIL_ScreenShake(self.vecimpactposition, self.ENV_HEADCRABCANISTER_SHAKE_AMPLITUDE, 150.0, 1.0, shakeRadius, SHAKE_START)

            # Do explosion effects
            if not self.HasSpawnFlags(self.SF_NO_IMPACT_EFFECTS):
                # Normal explosion
                ExplosionCreate( self.vecimpactposition, self.GetAbsAngles(), self, int(self.detonatedamage), int(self.detonatedamageradius), 
                    SF_ENVEXPLOSION_NODLIGHTS | SF_ENVEXPLOSION_NOSPARKS | SF_ENVEXPLOSION_NODAMAGE | SF_ENVEXPLOSION_NOSOUND, 1300.0 )
                    
                # Dust explosion
                #pExplosion = AR2Explosion.CreateAR2Explosion(self.vecimpactposition)
                
                #if pExplosion:
                #    pExplosion.SetLifetime(10)
                
            # Stun nearby enemies from detonation
            targets = UTIL_EntitiesInSphere(1024, self.GetAbsOrigin(), self.stunradius, FL_NPC)
            for target in targets:
                if not target or not target.IsAlive() or not target.IsUnit():
                    continue
                if random.random() > self.stunchance:
                    continue
                StunnedEffectInfo.CreateAndApply(target, attacker=self, duration=self.stunduration)
                
        def HeadcrabCanisterWorldThink(self):
            """ This think function simulates (moves/collides) the HeadcrabCanister while in
                the world. """
            # Get the current time.
            flTime = gpGlobals.curtime

            vecStartPosition = self.GetAbsOrigin()

            # Update HeadcrabCanister position for swept collision test.
            vecEndPosition = Vector()
            vecEndAngles = QAngle()
            self.GetPositionAtTime( flTime, vecEndPosition, vecEndAngles )

            if not self.incomingsoundstarted and not self.HasSpawnFlags(self.SF_NO_IMPACT_SOUND):
                flDistSq = self.ENV_HEADCRABCANISTER_INCOMING_SOUND_TIME * self.flightspeed
                flDistSq *= flDistSq
                if vecEndPosition.DistToSqr(self.vecimpactposition) <= flDistSq:
                    # Figure out if we're close enough to play the incoming sound
                    self.EmitSound( "HeadcrabCanister.IncomingSound" )
                    self.incomingsoundstarted = True

            # TODO
            #self.TestForCollisionsAgainstEntities(vecEndPosition)
            if self.DidImpact( flTime ):
                if not self.hasdetonated:
                    self.Detonate()
                    self.hasdetonated = True

                if not self.HasSpawnFlags(self.SF_REMOVE_ON_IMPACT):
                    self.Landed()

                return
                   
            # Always move full movement.
            self.SetAbsOrigin(vecEndPosition)

            # Touch triggers along the way
            self.PhysicsTouchTriggers(vecStartPosition)

            self.SetNextThink(gpGlobals.curtime + 0.2)
            self.SetAbsAngles(vecEndAngles)

            if not self.hasdetonated:
                if vecEndPosition.DistToSqr( self.vecimpactposition ) < self.BoundingRadius() * self.BoundingRadius():
                    self.Detonate()
                    self.hasdetonated = True

        def HeadcrabCanisterSkyboxThink(self):
            """ This think function should be called at the time when the HeadcrabCanister 
                will be leaving the skybox and entering the world. """
            # Use different position computation
            self.ConvertFromSkyboxToWorld()

            vecEndPosition = Vector()
            vecEndAngles = QAngle()
            self.GetPositionAtTime(gpGlobals.curtime, vecEndPosition, vecEndAngles)
            UTIL_SetOrigin(self, vecEndPosition)
            self.SetAbsAngles(vecEndAngles)
            self.RemoveEFlags(EFL_IN_SKYBOX)

            # Switch to the actual-scale model
            self.SetupWorldModel()

            # Futz with the smoke trail to get it working across the boundary
            self.trail.SetSkybox(vec3_origin, 1.0)

            # Now we start looking for collisions
            self.SetThink(self.HeadcrabCanisterWorldThink)
            self.SetNextThink(gpGlobals.curtime + 0.01)

        def HeadcrabCanisterSkyboxOnlyThink(self):
            """ This stops its motion in the skybox """
            vecEndPosition = Vector()
            vecEndAngles = QAngle()
            self.GetPositionAtTime(gpGlobals.curtime, vecEndPosition, vecEndAngles)
            UTIL_SetOrigin(self, vecEndPosition)
            self.SetAbsAngles(vecEndAngles)

            if not self.HasSpawnFlags(self.SF_NO_IMPACT_SOUND):
                filter = CPASAttenuationFilter(self, ATTN_NONE)
                self.EmitSoundFilter(filter, self.entindex(), "HeadcrabCanister.SkyboxExplosion")

            if self.skyboxcanistercount != 0:
                self.skyboxcanistercount -= 1
                if self.skyboxcanistercount <= 0:
                    SetThink(None)
                    return

            flRefireTime = random.uniform(self.minrefiretime, self.maxrefiretime) + self.ENV_HEADCRABCANISTER_TRAIL_TIME
            SetThink(self.HeadcrabCanisterSkyboxRestartThink)
            SetNextThink(gpGlobals.curtime + flRefireTime)

        def HeadcrabCanisterSkyboxRestartThink(self):
            """ This will re-fire the headcrab cannister """
            if self.trail:
                UTIL_Remove(self.trail)
                self.trail = None

            self.launched = False

            self.InputFireCanister(data)

        # Vars
        launched = False
        trail = None
        smoketrail = None
        
        # Fields
        headcrabtype = IntegerField(value=0, keyname='HeadcrabType')
        headcrabcount = IntegerField(value=0, keyname='HeadcrabCount')
        smokelifetime = FloatField(value=0.0, keyname='SmokeLifetime')
        launchpositionname = StringField(value='', keyname='LaunchPositionName')
        vecimpactposition = VectorField(value=vec3_origin)
        
        minrefiretime = FloatField(value=-1.0, keyname='MinSkyboxRefireTime')
        maxrefiretime = FloatField(value=-1.0, keyname='MaxSkyboxRefireTime')
        skyboxcanistercount = IntegerField(value=0.0, keyname='SkyboxCannisterCount')
        damageradius = FloatField(value=0.0, keyname='DamageRadius')
        damage = FloatField(value=0.0, keyname='Damage')
        detonatedamageradius = FloatField(value=300.0, keyname='DetonateDamageRadius')
        detonatedamage = FloatField(value=250.0, keyname='DetonateDamage')
        
        onlaunched = OutputField(keyname="OnLaunched" )
        onimpacted = OutputField(keyname="OnImpacted")
        onopened = OutputField(keyname="OnOpened")
        
    inskybox = False
        
    # Fields
    state = IntegerField(value=STATE_CLOSED, networked=True)
    landed = BooleanField(value=False, networked=True)
    launchheight = FloatField(value=0.0, keyname='StartingHeight', networked=True)
    
    flightspeed = FloatField(value=0.0, keyname='FlightSpeed', networked=True)
    launchtime = FloatField(value=-1.0, networked=True)
    vecparaboladirection = VectorField(value=vec3_origin, networked=True)
    
    flighttime = FloatField(value=1.0, keyname='FlightTime', networked=True)
    worldentertime = FloatField(value=0.0, keyname='FlightTime', networked=True)
    
    initialzspeed = FloatField(value=0.0, networked=True)
    zacceleration = FloatField(value=0.0, networked=True)
    horizspeed = FloatField(value=1600.0, networked=True) #speed
    launchedfromwithinworld = BooleanField(value=False, networked=True)
    
    vecstartposition = VectorField(value=Vector(0, 0, 0), networked=True)
    vecenterworldposition = VectorField(value=vec3_origin, networked=True)
    vecdirection = VectorField(value=Vector(0, 0, 0), networked=True)
    vecstartangles = QAngleField(value=vec3_angle, networked=True)
    
    stunradius = FloatField(value=128.0, keyname='StunRadius')
    stunduration = FloatField(value=3.0, keyname='StunDuration')
    stunchance = FloatField(value=1.01, keyname='StunChance')
        
    fowflags = FOWFLAG_UPDATER
    customeyeoffset = Vector(0,0,48)
    
    lifetime = FloatField(value=0)
    
    # Hook for modifying headcrab before or after spawning
    fnprespawnheadcrab = None
    fnpostspawnheadcrab = None
    
    #: Set by headcrab cannister launch ability and indicates the owner which fires the cannister.
    launcher_owner = None
        
    # Spawn flags
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_NO_IMPACT_SOUND', 0x1, False), 
         ('SF_NO_LAUNCH_SOUND', 0x2, False),
         ('SF_START_IMPACTED', 0x1000, False), 
         ('SF_LAND_AT_INITIAL_POSITION', 0x2000, False), 
         ('SF_WAIT_FOR_INPUT_TO_OPEN', 0x4000, False), 
         ('SF_WAIT_FOR_INPUT_TO_SPAWN_HEADCRABS', 0x8000, False), 
         ('SF_NO_SMOKE', 0x10000, False), 
         ('SF_NO_SHAKE', 0x20000, False), 
         ('SF_REMOVE_ON_IMPACT', 0x40000, False), 
         ('SF_NO_IMPACT_EFFECTS', 0x80000, False)], 
        cppimplemented=True)
        
    # Settings
    ENV_HEADCRABCANISTER_INCOMING_SOUND_TIME = 1.0
    ENV_HEADCRABCANISTER_TRAIL_TIME = 3.0
    
    ENV_HEADCRABCANISTER_SHAKE_AMPLITUDE = 50
    ENV_HEADCRABCANISTER_SHAKE_RADIUS = 1024
    ENV_HEADCRABCANISTER_SHAKE_RADIUS_VEHICLE = 2500
    
    ROTATION_SPEED = 90.0
    
    headcrabclass = [
        'unit_headcrab',
        'unit_headcrab_fast',
        'unit_headcrab_poison',
        'unit_headcrab_poison_boss',
    ]
        
    # Models
    ENV_HEADCRABCANISTER_MODEL = 'models/props_combine/headcrabcannister01a.mdl'
    ENV_HEADCRABCANISTER_BROKEN_MODEL = 'models/props_combine/headcrabcannister01b.mdl'
    ENV_HEADCRABCANISTER_SKYBOX_MODEL = 'models/props_combine/headcrabcannister01a_skybox.mdl'

class HeadcrabCanisterInfo(UnitInfo):
    name = 'unit_headcrabcanister'
    displayname = '#ZomHeadcrabCanister_Name'
    description = '#ZomHeadcrabCanister_Description'
    cls_name = 'unit_headcrabcanister'
    modelname = UnitHeadcrabCanister.ENV_HEADCRABCANISTER_MODEL
    hidden = True
    health = 100
    attackpriority = -1
    population = 0
    attributes = ['building', 'explosive_canister']