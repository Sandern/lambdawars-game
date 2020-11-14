from srcbase import *
from vmath import *
import random

from core.resources import UpdateResource
from wars_game.resources import ResGrubsInfo
from core.units import UnitInfo, UnitBase
from entities import Disposition_t, entity, FOWFLAG_ALL_MASK, FOWFLAG_HIDDEN, FOWFLAG_NOTRANSMIT
from fields import FlagsField

if isserver:
    from entities import CSprite, CreateRagGib, Activity, CTakeDamageInfo
    from utils import UTIL_GetLocalPlayer, UTIL_BloodDecalTrace, UTIL_SetSize, UTIL_PrecacheOther, UTIL_Remove, UTIL_SetOrigin, UTIL_TraceLine, trace_t
    from particles import DispatchParticleEffect, PrecacheParticleSystem
    
@entity('unit_antliongrub', networked=True)
class AntlionGrub(UnitBase):
    def __init__(self):
        super().__init__()

        self.flinchtime = 0.0
        self.nextsquealsoundtime = -1
        self.nextidlesoundtime = -1
        self.state = self.GRUB_STATE_IDLE
        self.isresourceactive = False
  
        self.SetCanBeSeen(False)
        
    def CreateGlow(self):
        # Create the glow sprite
        self.glowsprite = CSprite.SpriteCreate( "sprites/grubflare1.vmt", self.GetLocalOrigin(), False )
        assert( self.glowsprite )
        if self.glowsprite == None:
            return

        self.glowsprite.TurnOn()
        self.glowsprite.SetTransparency( RenderMode_t.kRenderWorldGlow, 156, 169, 121, 164, RenderFx_t.kRenderFxNoDissipation )
        self.glowsprite.SetScale( 0.5 )
        self.glowsprite.SetGlowProxySize( 16.0 )
        nAttachment = self.LookupAttachment( "glow" )
        self.glowsprite.SetParent( self, nAttachment )
        self.glowsprite.SetLocalOrigin( vec3_origin )
        self.glowsprite.SetOwnerNumber(self.GetOwnerNumber())
        
        # Don't uselessly animate, we're a static sprite!
        self.glowsprite.SetNextThink( TICK_NEVER_THINK )
        
    def FadeGlow(self):
        if self.glowsprite:
            self.glowsprite.FadeAndDie( 0.25 )

    def UpdateOnRemove(self):
        self.FadeGlow()
        
        if self.isresourceactive:
            # Remove one grub
            UpdateResource(self.GetOwnerNumber(), ResGrubsInfo.name, -1)
            if self.GetOwnerEntity():
                try: self.GetOwnerEntity().GrubDied(self)
                except AttributeError: pass
        
        # ALWAYS CHAIN BACK!
        super().UpdateOnRemove()
        
    def Event_Killed(self, info):
        self.SendOnKilledGameEvent( info )

        # Crush and crowbar damage hurt us more than others
        bSquashed = bool( info.GetDamageType() & (DMG_CRUSH|DMG_CLUB))
        self.Squash( info.GetAttacker(), False, bSquashed )

        self.takedamage = DAMAGE_NO

        #if sk_grubnugget_enabled.GetBool():
        #    self.CreateNugget()        # TODO: Support this? 

        # Go away
        self.SetThink( self.SUB_Remove )
        self.SetNextThink( gpGlobals.curtime + 0.1 )

        # we deliberately do not call super().EventKilled

    def OnTakeDamage(self, info):
    
        # Animate a flinch of pain if we're dying
        bSquashed = ( self.GetEffects() & EF_NODRAW ) != 0
        if bSquashed == False:
            self.SetSequence( self.SelectWeightedSequence( Activity.ACT_SMALL_FLINCH ) )
            self.flinchtime = gpGlobals.curtime + random.uniform( 0.5, 1.0 )

            self.SetThink( self.FlinchThink )
            self.SetNextThink( gpGlobals.curtime + 0.05 )

        return super().OnTakeDamage( info )

    def Spawn(self):
        super().Spawn()
        
        if isclient:
            return

        self.SetModel( self.ANTLIONGRUB_MODEL )
        
        # FIXME: This is a big perf hit with the number of grubs we're using! - jdw
        self.CreateGlow()

        self.SetSolid( SOLID_BBOX )
        self.SetSolidFlags( FSOLID_NOT_SOLID|FSOLID_TRIGGER )
        self.SetMoveType( MOVETYPE_NONE )
        self.SetCollisionGroup( COLLISION_GROUP_NONE )
        self.AddEffects( EF_NOSHADOW )

        self.CollisionProp().UseTriggerBounds(True,1)

        self.SetTouch( self.GrubTouch )

        #self.health = 1
        self.takedamage = DAMAGE_YES

        # Stick to the nearest surface
        if self.HasSpawnFlags( self.SF_ANTLIONGRUB_AUTO_PLACEMENT ):
            self.AttachToSurface()
            
        # Should we act as resource?
        if self.IsResource():
            self.isresourceactive = True
            UpdateResource(self.GetOwnerNumber(), ResGrubsInfo.name, 1)
            
        # At self point, alter our bounds to make sure we're within them
        vecMins = Vector()
        vecMaxs = Vector()
        RotateAABB( self.EntityToWorldTransform(), self.CollisionProp().OBBMins(), self.CollisionProp().OBBMaxs(), vecMins, vecMaxs )

        UTIL_SetSize( self, vecMins, vecMaxs )

        # Start our idle activity
        self.SetSequence( self.SelectWeightedSequence( Activity.ACT_IDLE ) )
        self.SetCycle( random.uniform( 0.0, 1.0 ) )
        self.ResetSequenceInfo()

        self.state = self.GRUB_STATE_IDLE

        # Reset
        self.flinchtime = 0.0
        self.nextidlesoundtime = gpGlobals.curtime + random.uniform( 4.0, 8.0 )
 
    def Activate(self):
        super().Activate()

        # Idly think
        #self.SetThink( self.IdleThink )
        #self.SetNextThink(gpGlobals.curtime + 3.0)

    def IsResource(self):
        return self.HasSpawnFlags( self.SF_ANTLIONGRUB_ISRESOURCE ) 
        
    def CanBeSeenBy(self, unit):
        """ Can't be seen by other units. We are simply not interesting """
        return False
        
    def IsSelectableByPlayer(self, player, target_selection):
        """ Grubs are not selectable """    
        return False

    def OnChangeOwnerNumber(self, old_owner_number):
        super().OnChangeOwnerNumber(old_owner_number)

        if isserver:
            if self.isresourceactive:
                # Old one decrement one grub, new one increment one grub
                UpdateResource( old_owner_number, ResGrubsInfo.name, -1)
                UpdateResource( self.GetOwnerNumber(), ResGrubsInfo.name, 1)
                
            if self.glowsprite:
                self.glowsprite.SetOwnerNumber(self.GetOwnerNumber())
            if self.GetOwnerNumber() == 0:
                self.RemoveFOWFlags(FOWFLAG_HIDDEN)
            else:
                self.AddFOWFlags(FOWFLAG_HIDDEN)
        
    def ProbeSurface(self, vecTestPos, vecDir, vecResult, vecNormal):
        # Trace down to find a surface
        tr = trace_t()
        UTIL_TraceLine( vecTestPos, vecTestPos + (vecDir*256.0), MASK_NPCSOLID&(~CONTENTS_MONSTER), self, COLLISION_GROUP_NONE, tr )
        
        if vecResult:
            vecResult = (tr.endpos)
        if vecNormal:
            vecNormal = (tr.plane.normal)

        return tr.fraction < 1.0

    def AttachToSurface(self):
        """ Attaches the grub to the surface underneath its abdomen """
        # Get our downward direction
        vecForward = Vector()
        vecRight = Vector()
        vecDown = Vector()
        self.GetVectors( vecForward, vecRight, vecDown )
        vecDown.Negate()
        
        vecOffset = ( vecDown * -8.0 )

        # Middle
        vecMid = Vector()
        vecMidNormal = Vector()
        if self.ProbeSurface( self.WorldSpaceCenter() + vecOffset, vecDown, vecMid, vecMidNormal ) == False:
            # A grub was left hanging in the air, it must not be near any valid surfaces!
            PrintWarning("Antlion grub stranded in space at ("+str(self.GetAbsOrigin().x)+", "+str(self.GetAbsOrigin().y)+", "+str(self.GetAbsOrigin().z)+") : REMOVED\n" )
            UTIL_Remove( self )
            return

        # Sit at the mid-point
        UTIL_SetOrigin( self, vecMid )

        vecPivot = Vector()
        vecPivotNormal = Vector()
        
        bNegate = True

        # First test our tail (more crucial that it doesn't interpenetrate with the world)
        if self.ProbeSurface( self.WorldSpaceCenter() - ( vecForward * 12.0 ) + vecOffset, vecDown, vecPivot, vecPivotNormal ) == False:
            # If that didn't find a surface, try the head
            if self.ProbeSurface( self.WorldSpaceCenter() + ( vecForward * 12.0 ) + vecOffset, vecDown, vecPivot, vecPivotNormal ) == False:
                # Worst case, just site at the middle
                UTIL_SetOrigin( self, vecMid )

                vecAngles = QAngle()
                VectorAngles( vecForward, vecMidNormal, vecAngles )
                self.SetAbsAngles( vecAngles )
                return   

            bNegate = False 
        
        # Find the line we'll lay on if these two points are connected by a line
        vecLieDir = ( vecPivot - vecMid )
        VectorNormalize( vecLieDir )
        if bNegate:
            # We need to try and maintain our facing
            vecLieDir.Negate()

        # Use the average of the surface normals to be our "up" direction
        vecPseudoUp = ( vecMidNormal + vecPivotNormal ) * 0.5

        vecAngles = QAngle()
        VectorAngles( vecLieDir, vecPseudoUp, vecAngles )

        self.SetAbsAngles( vecAngles )

    def MakeIdleSounds(self):
        if self.state == self.GRUB_STATE_AGITATED:
            if self.nextsquealsoundtime < gpGlobals.curtime:
                self.EmitSound( "NPC_Antlion_Grub.Stimulated" )
                self.nextsquealsoundtime = gpGlobals.curtime + random.uniform( 1.5, 3.0 )
                self.nextidlesoundtime = gpGlobals.curtime + random.uniform( 4.0, 8.0 )
        else:
            if self.nextidlesoundtime < gpGlobals.curtime:
                self.EmitSound( "NPC_Antlion_Grub.Idle" )
                self.nextidlesoundtime = gpGlobals.curtime + random.uniform( 8.0, 12.0 )
                
    def IdleThink(self):
        """ Advance our thinks """
        bFlinching = ( self.flinchtime > gpGlobals.curtime )

        bAgitated = ( bFlinching )

        # If we're idle and the player has come close enough, get agry
        if self.state == self.GRUB_STATE_IDLE and bAgitated:
            self.SetSequence( self.SelectWeightedSequence( Activity.ACT_SMALL_FLINCH ) )
            self.state = self.GRUB_STATE_AGITATED
        elif self.IsSequenceFinished():
            # See if it's time to choose a new sequence
            self.ResetSequenceInfo()
            self.SetCycle( 0.0 )

            # If we're near enough, we want to play an "alert" animation
            if bAgitated:
                self.SetSequence( self.SelectWeightedSequence( Activity.ACT_SMALL_FLINCH ) )
                self.state = self.GRUB_STATE_AGITATED
            else:
                # Just idle
                self.SetSequence( self.SelectWeightedSequence( Activity.ACT_IDLE ) )
                self.state = self.GRUB_STATE_IDLE

            # Add some variation because we're often in large bunches
            self.SetPlaybackRate( random.uniform( 0.8, 1.2 ) )

        # Idle normally
        self.StudioFrameAdvance()
        self.MakeIdleSounds()
        self.SetNextThink( gpGlobals.curtime + 0.1 )
    
    def FlinchThink(self):
        self.StudioFrameAdvance()
        self.SetNextThink( gpGlobals.curtime + 0.1 )

        # See if we're done
        if self.flinchtime < gpGlobals.curtime:
            self.SetSequence( self.SelectWeightedSequence( Activity.ACT_IDLE ) )
            self.SetThink( self.IdleThink )

    def GrubTouch(self, other):
        # We can be squished by the player, Vort, or flying heavy things.
        pPhysOther = other.VPhysicsGetObject() # bThrown = ( pTarget.VPhysicsGetObject().GetGameFlags() & FVPHYSICS_WAS_THROWN ) != 0
        if other.IsPlayer(): # or ( pPhysOther and (pPhysOther.GetGameFlags() & FVPHYSICS_WAS_THROWN )):
            self.Squash( other, True, True )
            
        elif self.GetOwnerNumber() == 0 and other == self.assignedtoworker and other.carryinggrub == None:
            assert( self.GetOwnerEntity() )
            self.GetOwnerEntity().GrubDied(self)
            self.SetOwnerEntity(other)
            self.SetParent(other, other.LookupAttachment( "mouth" ) )
            self.SetLocalOrigin(vec3_origin)
            self.SetLocalAngles(vec3_angle)
            other.Get().carryinggrub = self.GetHandle()
            
    def Precache(self):
        #self.PrecacheModel( self.ANTLIONGRUB_MODEL )
        self.PrecacheModel( self.ANTLIONGRUB_SQUASHED_MODEL )

        self.glowspritehandle = self.PrecacheModel("sprites/grubflare1.vmt")

        self.PrecacheScriptSound( "NPC_Antlion_Grub.Idle" )
        self.PrecacheScriptSound( "NPC_Antlion_Grub.Alert" )
        self.PrecacheScriptSound( "NPC_Antlion_Grub.Stimulated" )
        self.PrecacheScriptSound( "NPC_Antlion_Grub.Die" )
        self.PrecacheScriptSound( "NPC_Antlion_Grub.Squish" )

        if isserver:
            PrecacheParticleSystem( "GrubSquashBlood" )
            PrecacheParticleSystem( "GrubBlood" )

        # UTIL_PrecacheOther( "item_grubnugget" )   # Support this

        super().Precache()

    def SpawnSquashedGrub(self):
        # If we're already invisible, we're done
        if self.GetEffects() & EF_NODRAW:
            return

        vecUp = Vector()
        self.GetVectors( None, None, vecUp )
        pGib = CreateRagGib( self.ANTLIONGRUB_SQUASHED_MODEL, self.GetAbsOrigin(), self.GetAbsAngles(), vecUp * 16.0 )
        if pGib:
            pGib.AddEffects( EF_NOSHADOW )

    def MakeSquashDecals(self, vecOrigin):
        tr = trace_t()
        vecStart = Vector()
        vecTraceDir = Vector()
        
        self.GetVectors( None, None, vecTraceDir )
        vecTraceDir.Negate()

        for i in range(0, 8):
            vecStart.x = vecOrigin.x + random.uniform( -16.0, 16.0 )
            vecStart.y = vecOrigin.y + random.uniform( -16.0, 16.0 )
            vecStart.z = vecOrigin.z + 4

            UTIL_TraceLine( vecStart, vecStart + ( vecTraceDir * (5*12) ), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr )

            if tr.fraction != 1.0:
                UTIL_BloodDecalTrace( tr, BLOOD_COLOR_YELLOW )

    def Squash(self, pOther, bDealDamage, bSpawnBlood):
        # If we're already squashed, then don't bother doing it again!
        if self.GetEffects() & EF_NODRAW:
            return

        self.SpawnSquashedGrub()

        self.AddEffects( EF_NODRAW )
        self.AddSolidFlags( FSOLID_NOT_SOLID )
        
        # Stop being attached to us
        if self.glowsprite:
            self.FadeGlow()
            self.glowsprite.SetParent( None )

        self.EmitSound( "NPC_Antlion_Grub.Die" )
        self.EmitSound( "NPC_Antlion_Grub.Squish" )

        self.SetTouch( None )

        #if ( bSpawnBlood )
        if True:
            # Temp squash effect
            vecForward = Vector()
            vecUp = Vector()
            AngleVectors( self.GetAbsAngles(), vecForward, None, vecUp )
            
            # Start effects at either end of the grub
            vecSplortPos = self.GetAbsOrigin() + vecForward * 14.0
            DispatchParticleEffect( "GrubSquashBlood", vecSplortPos, self.GetAbsAngles() )

            vecSplortPos = self.GetAbsOrigin() - vecForward * 16.0
            vecDir = -vecForward
            vecAngles = QAngle()
            VectorAngles( vecDir, vecAngles )
            DispatchParticleEffect( "GrubSquashBlood", vecSplortPos, vecAngles )
            
            self.MakeSquashDecals( self.GetAbsOrigin() + vecForward * 32.0 )
            self.MakeSquashDecals( self.GetAbsOrigin() - vecForward * 32.0 )

        # Deal deadly damage to ourself
        if bDealDamage:
            info = CTakeDamageInfo( pOther, pOther, Vector( 0, 0, -1 ), self.GetAbsOrigin(), self.health+1, DMG_CRUSH )
            self.TakeDamage( info )
        
    def TraceAttack(self, info, vecDir, tr):
        vecAngles = QAngle()
        VectorAngles( -vecDir, vecAngles )
        DispatchParticleEffect( "GrubBlood", tr.endpos, vecAngles )

        super().TraceAttack( info, vecDir, tr )

    # Settings
    fowflags = FOWFLAG_NOTRANSMIT
    ANTLIONGRUB_MODEL = "models/antlion_grub.mdl"
    ANTLIONGRUB_SQUASHED_MODEL = "models/antlion_grub_squashed.mdl"

    # Spawn flags
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_ANTLIONGRUB_AUTO_PLACEMENT', ( 1 << 16 ), False), 
         ('SF_ANTLIONGRUB_ISRESOURCE', ( 1 << 17 ), False)], 
        cppimplemented=True)
        
    GRUB_STATE_IDLE = 0
    GRUB_STATE_AGITATED = 1
    
    # Default variables
    assignedtoworker = None
    glowsprite = None

# Register unit
class AntlionGrubInfo(UnitInfo):
    cls_name    ="unit_antliongrub"
    attributes = ['slash']
    image_name = "vgui/units/unit_antliongrub.vmt"
    displayname = "#AntlionGrub_Name"
    description = "#AntlionGrub_Description"
    modelname = 'models/antlion_grub.mdl'
    viewdistance = 256.0
    health = 1
    mins = Vector(-28.213966, -11.130074, -3.443373)
    maxs = Vector(17.651766, 13.017019, 12.114547)
    
class AntlionGrubResourceInfo(AntlionGrubInfo):
    name        ="unit_antliongrub_resource"
    keyvalues = {'spawnflags' : str(AntlionGrub.SF_ANTLIONGRUB_ISRESOURCE)}
    population = 0      # Don't consume any population
