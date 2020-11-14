from srcbase import *
from vmath import (Vector, QAngle, matrix3x4_t, vec3_origin, ConcatTransforms, MatrixInvert, MatrixAngles,
                   VectorNormalize, AngleVectors)
import random
from entities import networked
from core.units import UnitBaseCombat as BaseClass, UnitInfo, CreateUnitNoSpawn, PrecacheUnit
from utils import UTIL_TraceHull, trace_t, UTIL_ShouldShowBlood, UTIL_BloodDrips, UTIL_BloodImpact

if isserver:
    from entities import SpawnBlood, g_vecAttackDir, CreateRagGib, DispatchSpawn
    from particles import PrecacheParticleSystem
    from utils import UTIL_SetSize

@networked
class UnitBaseZombie(BaseClass):
    def Spawn(self):
        super().Spawn()
        
        self.SetBloodColor(BLOOD_COLOR_ZOMBIE)
            
    if isserver:
        def Precache(self):
            super().Precache() 
            
            PrecacheUnit(self.headcrabclassname)

            self.PrecacheModel(self.headcrabmodel)
            self.PrecacheScriptSound("E3_Phystown.Slicer")
            self.PrecacheScriptSound("NPC_BaseZombie.PoundDoor")
            self.PrecacheScriptSound("NPC_BaseZombie.Swat")

            PrecacheParticleSystem("blood_impact_zombie_01")
            
        @classmethod
        def PrecacheUnitType(cls, info):
            super().PrecacheUnitType(info)
            
            cls.PrecacheModel(info.legmodel)
            cls.PrecacheModel(info.torsomodel)
            cls.PrecacheModel(info.torsogibmodel)
 
        def SetUnitModel(self, modelname=None, *args, **kwargs):
            unitinfo = self.unitinfo
            if modelname:
                self.SetModel(modelname)
            elif self.istorso:
                self.SetModel(unitinfo.torsomodel)
            else:
                self.SetModel(unitinfo.modelname)
                
            self.SetBodygroup(self.ZOMBIE_BODYGROUP_HEADCRAB, not self.isheadless)
                
            if self.GetModelScale() != unitinfo.scale:
                self.SetModelScale(unitinfo.scale)
                
            if self.GetSolid() == SOLID_BBOX:
                UTIL_SetSize(self, unitinfo.mins, unitinfo.maxs)
            
    def ClawAttack(self, flDist, iDamage, qaViewPunch, vecVelocityPunch, BloodOrigin):
        """ Look in front and see if the claw hit anything. 
        
            Input:
            flDist: distance to trace
            iDamage: damage to do if attack hits
            vecViewPunch: camera punch (if attack hits player)
            vecVelocityPunch: velocity punch (if attack hits player)
            
            Output:
            The entity hit by claws. None if nothing.
        """
        # Added test because claw attack anim sometimes used when for cases other than melee
        iDriverInitialHealth = -1
        pDriver = None
        if self.enemy:
            tr = trace_t()
            UTIL_TraceHull(self.WorldSpaceCenter(), self.enemy.EyePosition(), -Vector(8,8,8), Vector(8,8,8), MASK_SOLID_BRUSHONLY, self, COLLISION_GROUP_NONE, tr)
            if tr.fraction < 1.0:
                return None

            # CheckTraceHullAttack() can damage player in vehicle as side effect of melee attack damaging physics objects, which the car forwards to the player
            # need to detect self to get correct damage effects
            '''
            pCCEnemy = ( self.enemy != None ) ? self.enemy.MyCombatCharacterPointer() : None
            CBaseEntity *pVehicleEntity
            if pCCEnemy != None and ( pVehicleEntity = pCCEnemy.GetVehicleEntity() ) != None:
                if ( pVehicleEntity.GetServerVehicle() and dynamic_cast<CPropVehicleDriveable *>(pVehicleEntity) )
                    pDriver = static_cast<CPropVehicleDriveable *>(pVehicleEntity).GetDriver()
                    if pDriver and pDriver.IsPlayer():
                        iDriverInitialHealth = pDriver.GetHealth()
                    else:
                        pDriver = None
            '''

        #
        # Trace out a cubic section of our hull and see what we hit.
        #
        vecMins = self.WorldAlignMins()
        vecMaxs = self.WorldAlignMaxs()
        vecMins.z = vecMins.x
        vecMaxs.z = vecMaxs.x

        '''
        pHurt = None
        if self.enemy and self.enemy.Classify() == CLASS_BULLSEYE:
            # We always hit bullseyes we're targeting
            pHurt = self.enemy
            CTakeDamageInfo info( self, self, vec3_origin, GetAbsOrigin(), iDamage, DMG_SLASH )
            pHurt.TakeDamage( info )
        else:
            # Try to hit them with a trace
        '''
        pHurt = self.CheckTraceHullAttack(flDist, vecMins, vecMaxs, iDamage, DMG_SLASH)

        '''
        if pDriver and iDriverInitialHealth != pDriver.GetHealth():
            pHurt = pDriver
        '''
        
        '''
        if not pHurt and self.physicsent != None and IsCurSchedule(SCHED_ZOMBIE_ATTACKITEM) )
            pHurt = self.physicsent

            Vector vForce = pHurt.WorldSpaceCenter() - WorldSpaceCenter() 
            VectorNormalize( vForce )

            vForce *= 5 * 24

            CTakeDamageInfo info( self, self, vForce, GetAbsOrigin(), iDamage, DMG_SLASH )
            pHurt.TakeDamage( info )

            pHurt = self.physicsent
        '''

        if pHurt:
            self.AttackHitSound()

            pPlayer = pHurt if pHurt.IsPlayer() else None

            if pPlayer != None and not (pPlayer.GetFlags() & FL_GODMODE ):
                pPlayer.ViewPunch( qaViewPunch )
                
                pPlayer.VelocityPunch( vecVelocityPunch )
            elif not pPlayer and UTIL_ShouldShowBlood(pHurt.BloodColor()):
                # Hit an NPC. Bleed them!
                vecBloodPos = Vector()

                if BloodOrigin == self.ZOMBIE_BLOOD_LEFT_HAND:
                    if self.GetAttachment( "blood_left", vecBloodPos ):
                        SpawnBlood(vecBloodPos, g_vecAttackDir, pHurt.BloodColor(), min(iDamage, 30))
                elif BloodOrigin == self.ZOMBIE_BLOOD_RIGHT_HAND:
                    if self.GetAttachment("blood_right", vecBloodPos):
                        SpawnBlood(vecBloodPos, g_vecAttackDir, pHurt.BloodColor(), min(iDamage,30))
                elif BloodOrigin == self.ZOMBIE_BLOOD_BOTH_HANDS:
                    if self.GetAttachment("blood_left", vecBloodPos):
                        SpawnBlood( vecBloodPos, g_vecAttackDir, pHurt.BloodColor(), min( iDamage, 30 ) )
                    if self.GetAttachment("blood_right", vecBloodPos):
                        SpawnBlood(vecBloodPos, g_vecAttackDir, pHurt.BloodColor(), min(iDamage, 30))
                #elif BloodOrigin == ZOMBIE_BLOOD_BITE:
                    # No blood for these.
        else:
            self.AttackMissSound()
        
        return pHurt
        
    #-----------------------------------------------------------------------------
    # Purpose: A zombie has taken damage. Determine whether he should split in half
    # Input  : 
    # Output : bool, true if yes.
    #-----------------------------------------------------------------------------
    def ShouldBecomeTorso(self, info, flDamageThreshold):
        if info.GetDamageType() & DMG_REMOVENORAGDOLL:
            return False

        if self.istorso:
            # Already split.
            return False

        # Not if we're in a dss
        #if self.IsRunningDynamicInteraction():
        #    return false

        # Break in half IF:
        # 
        # Take half or more of max health in DMG_BLAST
        if (info.GetDamageType() & DMG_BLAST) and flDamageThreshold >= 0.5:
            return True

        # Always split after a cannon hit
        #if ( info.GetAmmoType() == GetAmmoDef()->Index("CombineHeavyCannon") )
        #    return true
        
        return False
        
    #-----------------------------------------------------------------------------
    # Purpose: A zombie has taken damage. Determine whether he release his headcrab.
    # Output : YES, IMMEDIATE, or SCHEDULED (see HeadcrabRelease_t)
    #-----------------------------------------------------------------------------
    def ShouldReleaseHeadcrab(self, info, flDamageThreshold):
        if self.health <= 0:
            if info.GetDamageType() & DMG_REMOVENORAGDOLL:
                return 'RELEASE_NO'

            if info.GetDamageType() & DMG_SNIPER:
                return 'RELEASE_RAGDOLL'

            # If I was killed by a bullet...
            if info.GetDamageType() & DMG_BULLET:
                if self.headshot:
                    if flDamageThreshold > 0.25:
                        # Enough force to kill the crab.
                        return 'RELEASE_RAGDOLL'
                else:
                    # Killed by a shot to body or something. Crab is ok!
                    return 'RELEASE_IMMEDIATE'

            # If I was killed by an explosion, release the crab.
            if info.GetDamageType() & DMG_BLAST:
                return 'RELEASE_RAGDOLL'
            #if self.istorso and self.IsChopped(info):
            #    return 'RELEASE_RAGDOLL_SLICED_OFF'
        return 'RELEASE_NO'
        
    def IsChopped(self, info):
        return self.ischopped
        
    def IsSquashed(self, info):
        return False
        
    def BecomeRagdoll(self, info, forceVector):
        bKilledByVehicle = ( ( info.GetDamageType() & DMG_VEHICLE ) != 0 )
        if self.istorso or (not self.IsChopped(info) and not self.IsSquashed(info)) or bKilledByVehicle:
            return super().BecomeRagdoll(info, forceVector)

        if not (self.GetFlags()&FL_TRANSRAGDOLL):
            self.RemoveDeferred()

        return True

    #-----------------------------------------------------------------------------
    # Purpose: 
    # Input  : pInflictor - 
    #			pAttacker - 
    #			flDamage - 
    #			bitsDamageType - 
    # Output : int
    #-----------------------------------------------------------------------------
    ZOMBIE_SCORCH_RATE = 8
    ZOMBIE_MIN_RENDERCOLOR = 50
    def OnTakeDamage_Alive(self, inputInfo):
        info = inputInfo

        if inputInfo.GetDamageType() & DMG_BURN:
            # If a zombie is on fire it only takes damage from the fire that's attached to it. (DMG_DIRECT)
            # This is to stop zombies from burning to death 10x faster when they're standing around
            # 10 fire entities.
            if self.IsOnFire() and not (inputInfo.GetDamageType() & DMG_DIRECT):
                return 0

            self.Scorch(self.ZOMBIE_SCORCH_RATE, self.ZOMBIE_MIN_RENDERCOLOR)

        # Take some percentage of damage from bullets (unless hit in the crab). Always take full buckshot & sniper damage
        #if not self.headshot and (info.GetDamageType() & DMG_BULLET) and not (info.GetDamageType() & (DMG_BUCKSHOT|DMG_SNIPER)):
        #    info.ScaleDamage(self.ZOMBIE_BULLET_DAMAGE_SCALE)

        if self.ShouldIgnite(info):
            self.IgniteLifetime(100.0)

        tookDamage = super().OnTakeDamage_Alive(info)

        # flDamageThreshold is what percentage of the creature's max health
        # this amount of damage represents. (clips at 1.0)
        flDamageThreshold = min(1, info.GetDamage() / self.maxhealth)
        
        # Being chopped up by a sharp physics object is a pretty special case
        # so we handle it with some special code. Mainly for 
        # Ravenholm's helicopter traps right now (sjb).
        bChopped = self.IsChopped(info)
        bSquashed = self.IsSquashed(info)
        bKilledByVehicle = ( ( info.GetDamageType() & DMG_VEHICLE ) != 0 )

        if not self.istorso and (bChopped or bSquashed) and not bKilledByVehicle and not (info.GetDamageType() & DMG_REMOVENORAGDOLL):
            if bChopped:
                self.EmitSound( "E3_Phystown.Slicer" )

            self.DieChopped(info)
        else:
            release = self.ShouldReleaseHeadcrab(info, flDamageThreshold)

            if release == 'RELEASE_IMMEDIATE':
                self.ReleaseHeadcrab(self.EyePosition(), vec3_origin, True, True)
            elif release == 'RELEASE_RAGDOLL':
                # Go a little easy on headcrab ragdoll force. They're light!
                self.ReleaseHeadcrab(self.EyePosition(), inputInfo.GetDamageForce() * 0.25, True, False, True)
            elif release == 'RELEASE_RAGDOLL_SLICED_OFF':
                self.EmitSound( "E3_Phystown.Slicer" )
                vecForce = inputInfo.GetDamageForce() * 0.1
                vecForce += Vector(0, 0, 2000.0)
                self.ReleaseHeadcrab(self.EyePosition(), vecForce, True, False, True)

            elif release == 'RELEASE_VAPORIZE':
                self.RemoveHead()
                
            if self.ShouldBecomeTorso(info, flDamageThreshold):
                bHitByCombineCannon = False #(inputInfo.GetAmmoType() == self.GetAmmoDef().Index("CombineHeavyCannon"))

                if self.canbecomelivetorso:
                    self.BecomeTorso(vec3_origin, inputInfo.GetDamageForce() * 0.50)

                    if (info.GetDamageType() & DMG_BLAST) and random.randint( 0, 1 ) == 0:
                        self.IgniteLifetime(5.0 + random.uniform(0.0, 5.0))

                    # For Combine cannon impacts
                    if bHitByCombineCannon:
                        # Catch on fire.
                        self.IgniteLifetime(5.0 + random.uniform(0.0, 5.0))

                    if flDamageThreshold >= 1.0:
                        self.health = 0
                        self.BecomeRagdollOnClient(info.GetDamageForce())
                elif random.randint(1, 3) == 1:
                    self.DieChopped(info)

        #if tookDamage > 0 and (info.GetDamageType() & (DMG_BURN|DMG_DIRECT)): 
            #!!!HACKHACK- Stuff a light_damage condition if an actbusying zombie takes direct burn damage. This will cause an
            # ignited zombie to 'wake up' and rise out of its actbusy slump. (sjb)
        #    SetCondition( COND_LIGHT_DAMAGE )
        

        # IMPORTANT: always clear the headshot flag after applying damage. No early outs!
        self.headshot = False

        return tookDamage
        
    def ShouldIgniteZombieGib(self):
        return self.IsOnFire()

    def DieChopped(self, info):
        ''' Handle the special case of a zombie killed by a physics chopper. '''
        self.health = 0 # Make sure we will be killed!
        self.ischopped = True # Make sure we don't spawn another ragdoll!
        
        bSquashed = self.IsSquashed(info)

        forceVector = Vector(vec3_origin)

        forceVector += info.GetDamageForce() #CalcDamageForceVector( info )

        if not self.isheadless and not bSquashed:
            if random.randint( 0, 1 ) == 0:
                # Drop a live crab half of the time.
                self.ReleaseHeadcrab(self.EyePosition(), forceVector * 0.005, True, False, False)

        #flFadeTime = 0.0
        #if self.HasSpawnFlags( SF_NPC_FADE_CORPSE ):
        flFadeTime = 5.0

        self.SetSolid(SOLID_NONE)
        self.AddEffects(EF_NODRAW)

        vecLegsForce = Vector()
        vecLegsForce.x = random.uniform( -400, 400 )
        vecLegsForce.y = random.uniform( -400, 400 )
        vecLegsForce.z = random.uniform( 0, 250 )

        if bSquashed and vecLegsForce.z > 0:
            # Force the broken legs down. (Give some additional force, too)
            vecLegsForce.z *= -10

        pLegGib = CreateRagGib( self.unitinfo.legmodel, self.GetAbsOrigin(), self.GetAbsAngles(), vecLegsForce, flFadeTime, self.ShouldIgniteZombieGib())
        if pLegGib:
            self.CopyRenderColorTo(pLegGib)

        forceVector *= random.uniform( 0.04, 0.06 )
        forceVector.z = ( 100 * 12 * 5 ) * random.uniform(0.8, 1.2)

        if bSquashed and forceVector.z > 0:
            # Force the broken torso down.
            forceVector.z *= -1.0

        # Why do I have to fix this up?! (sjb)
        TorsoAngles = self.GetAbsAngles()
        TorsoAngles.x -= 90.0
        pTorsoGib = CreateRagGib( self.unitinfo.torsogibmodel, self.GetAbsOrigin() + Vector( 0, 0, 64 ), TorsoAngles, forceVector, flFadeTime, self.ShouldIgniteZombieGib())
        if pTorsoGib:
            pAnimating = pTorsoGib
            if pAnimating:
                pAnimating.SetBodygroup(self.ZOMBIE_BODYGROUP_HEADCRAB, not self.isheadless )

            pTorsoGib.SetOwnerEntity( self )
            self.CopyRenderColorTo( pTorsoGib )

        if UTIL_ShouldShowBlood(BLOOD_COLOR_YELLOW):
            vecDir = Vector()

            for i in range(0, 4):
                vecSpot = self.WorldSpaceCenter()

                vecSpot.x += random.uniform( -12, 12 ) 
                vecSpot.y += random.uniform( -12, 12 ) 
                vecSpot.z += random.uniform( -4, 16 ) 

                UTIL_BloodDrips( vecSpot, vec3_origin, BLOOD_COLOR_YELLOW, 50 )

            for i in range(0, 4):
                vecSpot = self.WorldSpaceCenter()

                vecSpot.x += random.uniform( -12, 12 ) 
                vecSpot.y += random.uniform( -12, 12 ) 
                vecSpot.z += random.uniform( -4, 16 )

                vecDir.x = random.uniform(-1, 1)
                vecDir.y = random.uniform(-1, 1)
                vecDir.z = 0
                VectorNormalize( vecDir )

                UTIL_BloodImpact( vecSpot, vecDir, self.BloodColor(), 1 )
            
    def ShouldIgnite(self, info):
        ''' damage has been done. Should the zombie ignite? '''
        if self.IsOnFire():
            # Already burning!
            return False

        if info.GetDamageType() & DMG_BURN:
            #
            # If we take more than ten percent of our health in burn damage within a five
            # second interval, we should catch on fire.
            #
            self.burndamage += info.GetDamage()
            self.burndamageresettime = gpGlobals.curtime + 5

            if self.burndamage >= self.maxhealth * 0.1:
                return True
        return False
        
    def UpdateTranslateActivityMap(self):
        if self.IsOnFire() and 'ignited' in self.acttransmaps:
            table = self.acttransmaps['ignited']
            self.animstate.SetActivityMap(table)
            return
        super().UpdateTranslateActivityMap()

    #-----------------------------------------------------------------------------
    # Purpose: Sufficient fire damage has been done. Zombie ignites!
    #-----------------------------------------------------------------------------
    def Ignite(self, flFlameLifetime, bNPCOnly, flSize, bCalledByLevelDesigner):
        super().Ignite( flFlameLifetime, bNPCOnly, flSize, bCalledByLevelDesigner )

    #ifdef HL2_EPISODIC
    #    if HL2GameRules().IsAlyxInDarknessMode() == True and GetEffectEntity() != None: 
    #        GetEffectEntity().AddEffects( EF_DIMLIGHT ) 
    #endif # HL2_EPISODIC

        # Set the zombie up to burn to death in about ten seconds.
        self.health = min(self.health, FLAME_DIRECT_DAMAGE_PER_SEC * (ZOMBIE_BURN_TIME + random.uniform(-ZOMBIE_BURN_TIME_NOISE, ZOMBIE_BURN_TIME_NOISE)))

        self.UpdateTranslateActivityMap()
        
        '''
        # FIXME: use overlays when they come online
        #AddOverlay( ACT_ZOM_WALK_ON_FIRE, False )
        if( !m_ActBusyBehavior.IsActive() )
        
            Activity activity = GetActivity()
            Activity burningActivity = activity

            if ( activity == ACT_WALK )
            
                burningActivity = ACT_WALK_ON_FIRE
            
            else if ( activity == ACT_RUN )
            
                burningActivity = ACT_RUN_ON_FIRE
            
            else if ( activity == ACT_IDLE )
            
                burningActivity = ACT_IDLE_ON_FIRE
            

            if( HaveSequenceForActivity(burningActivity) )
            
                # Make sure we have a sequence for this activity (torsos don't have any, for instance) 
                # to prevent the baseNPC & baseAnimating code from throwing red level errors.
                SetActivity( burningActivity )
        '''
        
    def CopyRenderColorTo(self, other):
        pass # FIXME
        #color = self.GetRenderColor()
        #other.SetRenderColor(color.r, color.g, color.b, color.a)

    def HeadcrabFits(self, crab):
        return True
        
    #-----------------------------------------------------------------------------
    # Purpose: 
    # Input  : &vecOrigin - 
    #			&vecVelocity - 
    #			fRemoveHead - 
    #			fRagdollBody - 
    #-----------------------------------------------------------------------------
    def ReleaseHeadcrab(self, vecOrigin, vecVelocity, fRemoveHead, fRagdollBody, fRagdollCrab=False):
        #return
        pCrab = None
        vecSpot = Vector(vecOrigin)

        # Until the headcrab is a bodygroup, we have to approximate the
        # location of the head with magic numbers.
        if not self.istorso:
            vecSpot.z -= 16

        if fRagdollCrab:
            #Vector vecForce = Vector( 0, 0, random.uniform( 700, 1100 ) )
            pGib = CreateRagGib(self.headcrabmodel, vecOrigin, self.GetLocalAngles(), vecVelocity, 15, self.ShouldIgniteZombieGib())

            if pGib:
                pAnimatingGib = pGib

                # don't collide with this thing ever
                iCrabAttachment = self.LookupAttachment( "headcrab" )
                if iCrabAttachment > 0 and pAnimatingGib:
                    self.SetHeadcrabSpawnLocation( iCrabAttachment, pAnimatingGib )

                if not self.HeadcrabFits(pAnimatingGib):
                    UTIL_Remove(pGib)
                    return

                pGib.SetOwnerEntity( self )
                self.CopyRenderColorTo( pGib )
                
                if UTIL_ShouldShowBlood(BLOOD_COLOR_YELLOW):
                    UTIL_BloodImpact( pGib.WorldSpaceCenter(), Vector(0,0,1), BLOOD_COLOR_YELLOW, 1 )

                    for i in range(0, 3):
                        vecSpot = pGib.WorldSpaceCenter()
                        
                        vecSpot.x += random.uniform( -8, 8 ) 
                        vecSpot.y += random.uniform( -8, 8 ) 
                        vecSpot.z += random.uniform( -8, 8 ) 

                        UTIL_BloodDrips( vecSpot, vec3_origin, BLOOD_COLOR_YELLOW, 50 )
        else:
            pCrab = CreateUnitNoSpawn(self.headcrabclassname, self.GetOwnerNumber())
            if not pCrab:
                PrintWarning("**%s: Can't make %s!\n" % (self.GetClassname(), self.headcrabclassname))
                return

            # don't pop to floor, fall
            #pCrab.AddSpawnFlags(SF_NPC_FALL_TO_GROUND)
            
            # add on the parent flags
            pCrab.AddSpawnFlags(self.GetSpawnFlags() & self.ZOMBIE_CRAB_INHERITED_SPAWNFLAGS)
            
            # make me the crab's owner to avoid collision issues
            pCrab.SetOwnerEntity(self)

            pCrab.SetAbsOrigin(vecSpot)
            pCrab.SetAbsAngles(self.GetAbsAngles())
            DispatchSpawn(pCrab)

            # FIXME: npc's with multiple headcrabs will need some way to query different attachments.
            # NOTE: this has till after spawn is called so that the model is set up
            iCrabAttachment = self.LookupAttachment( "headcrab" )
            if iCrabAttachment > 0:
                self.SetHeadcrabSpawnLocation(iCrabAttachment, pCrab)
                #pCrab.GetMotor().SetIdealYaw(pCrab.GetAbsAngles().y)
                
                # Take out any pitch
                angles = pCrab.GetAbsAngles()
                angles.x = 0.0
                pCrab.SetAbsAngles(angles)
                
            if not self.HeadcrabFits(pCrab):
                UTIL_Remove(pCrab)
                return
            
            pCrab.SetNextThink(gpGlobals.curtime)
            pCrab.PhysicsSimulate()
            pCrab.SetAbsVelocity(vecVelocity)

            # if I have an enemy, stuff that to the headcrab.
            pEnemy = self.enemy

            pCrab.nextattack = gpGlobals.curtime + 1.0

            if pEnemy:
                pCrab.enemy = pEnemy
            
            #if self.ShouldIgniteZombieGib():
            #    pCrab.Ignite( 30 )

            self.CopyRenderColorTo( pCrab )

            pCrab.Activate()
 
        if fRemoveHead:
            self.RemoveHead()

        if fRagdollBody:
            self.BecomeRagdollOnClient(vec3_origin)

    def RemoveHead(self):
        self.isheadless = True
        self.SetUnitModel()
        
    def SetHeadcrabSpawnLocation(self, iCrabAttachment, pCrab):
        assert(iCrabAttachment > 0)

        # get world location of intended headcrab root bone
        attachmentToWorld = matrix3x4_t()
        self.GetAttachment(iCrabAttachment, attachmentToWorld)

        # find offset of root bone from origin 
        pCrab.SetAbsOrigin(Vector(0, 0, 0))
        pCrab.SetAbsAngles(QAngle(0, 0, 0))
        pCrab.InvalidateBoneCache()
        rootLocal =  matrix3x4_t()
        pCrab.GetBoneTransform(0, rootLocal)

        # invert it
        rootInvLocal =  matrix3x4_t()
        MatrixInvert(rootLocal, rootInvLocal)

        # find spawn location needed for rootLocal transform to match attachmentToWorld
        spawnOrigin = matrix3x4_t()
        ConcatTransforms(attachmentToWorld, rootInvLocal, spawnOrigin)

        # reset location of headcrab
        vecOrigin = Vector()
        vecAngles = QAngle()
        MatrixAngles(spawnOrigin, vecAngles, vecOrigin)
        pCrab.SetAbsOrigin(vecOrigin)
        
        # FIXME: head crabs don't like pitch or roll!
        vecAngles.z = 0

        pCrab.SetAbsAngles(vecAngles)
        pCrab.InvalidateBoneCache()
        
    def IsSquashed(self, info):
        return False
        
    def AttackRight(self, event):
        right = Vector()
        forward = Vector()
        AngleVectors(self.GetLocalAngles(), forward, right, None)
        right = right * 100
        forward = forward * 200

        attackinfo = self.unitinfo.AttackMelee
        self.ClawAttack(attackinfo.maxrange, attackinfo.damage, QAngle(-15, -20, -10), right + forward, self.ZOMBIE_BLOOD_RIGHT_HAND)
        
    def AttackLeft(self, event):
        right = Vector()
        forward = Vector()
        AngleVectors(self.GetLocalAngles(), forward, right, None)
        right = right * -100
        forward = forward * 200
        attackinfo = self.unitinfo.AttackMelee
        self.ClawAttack(attackinfo.maxrange, attackinfo.damage, QAngle(-15, 20, -10), right + forward, self.ZOMBIE_BLOOD_LEFT_HAND)
        
    def AttackBoth(self, event):
        forward = Vector()
        qaPunch = QAngle(45, random.uniform(-5,5), random.uniform(-5,5))
        AngleVectors(self.GetLocalAngles(), forward)
        forward = forward * 200
        attackinfo = self.unitinfo.AttackMelee
        self.ClawAttack(attackinfo.maxrange, attackinfo.damage, qaPunch, forward, self.ZOMBIE_BLOOD_BOTH_HANDS)
        
    if isserver:
        # AI, override die action
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionDie(BaseClass.BehaviorGenericClass.ActionDie):
                def OnStart(self):
                    pass
                        
                def OnResume(self):
                    pass
                    
        # Anim events
        aetable = {
            'AE_ZOMBIE_ATTACK_RIGHT' : AttackRight,
            'AE_ZOMBIE_ATTACK_LEFT' : AttackLeft,
            'AE_ZOMBIE_ATTACK_BOTH' : AttackBoth,
        }

    physicsent = None
    nextswat = 0.0
    burndamage = 0.0
    
    istorso = False
    isheadless = False
    headshot = False

    ZOMBIE_BODYGROUP_HEADCRAB = 1 # The crab on our head

    ZOMBIE_CRAB_INHERITED_SPAWNFLAGS = 0
    
    ZOMBIE_BULLET_DAMAGE_SCALE = 0.5
    
    # Pass these to claw attack so we know where to draw the blood.
    ZOMBIE_BLOOD_LEFT_HAND = 0
    ZOMBIE_BLOOD_RIGHT_HAND = 1
    ZOMBIE_BLOOD_BOTH_HANDS = 2
    ZOMBIE_BLOOD_BITE = 3
    
    # Activities
    acttables = dict(BaseClass.acttables)
    acttables.update({

    })
    
    # Settings
    headcrabclassname = 'unit_headcrab'
    headcrabmodel = 'models/headcrabclassic.mdl'
    canbecomelivetorso = False
    ischopped = False
    
class BaseZombieInfo(UnitInfo):
    legmodel = 'models/zombie/classic_legs.mdl'
    torsomodel = 'models/zombie/classic_torso.mdl'
    torsogibmodel = 'models/zombie/classic_torso.mdl'
    attributes = ['light', 'creature']
    hulltype = 'HULL_HUMAN'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    