from srcbase import MAX_TRACE_LENGTH, DMG_CLUB, MASK_ALL, MASK_SHOT_HULL, COLLISION_GROUP_NONE, CONTENTS_WATER, CONTENTS_SLIME
from vmath import Vector, vec3_origin, VectorNormalize
from .base import WarsWeaponBase as BaseClass
from entities import MELEE_HIT, SINGLE, Activity
from te import CEffectData, DispatchEffect
from utils import UTIL_TraceLine, trace_t, UTIL_ImpactTrace, UTIL_TraceHull, UTIL_PointContents
from entities import ACT_VM_MISSCENTER2, ACT_VM_MISSCENTER, ACT_VM_HITCENTER, CalculateMeleeDamageForce, ApplyMultiDamage

if isserver:
    from entities import CTakeDamageInfo
    
FX_WATER_IN_SLIME = 0x1

class WarsWeaponMelee(BaseClass):
    """ Weapon base for melee like weapons. """
    class AttackPrimary(BaseClass.AttackMelee):
        damage = 5.0
        maxrange = 32.0
    
    BLUDGEON_HULL_DIM = 16

    bludgeonmins = Vector(-BLUDGEON_HULL_DIM,-BLUDGEON_HULL_DIM,-BLUDGEON_HULL_DIM)
    bludgeonmaxs = Vector(BLUDGEON_HULL_DIM,BLUDGEON_HULL_DIM,BLUDGEON_HULL_DIM)

    def PrimaryAttack(self):
        self.Swing(False)

    def SecondaryAttack(self):
        self.Swing(True)

    def Hit(self, traceHit, nHitActivity):
        """ Implement impact function """
        owner = self.GetOwner()
        
        #Do view kick
    #	AddViewKick()

        pHitEntity = traceHit.ent

        #Apply damage to a hit target
        if pHitEntity != None:
            swingStart, hitDirection = self.GetShootOriginAndDirection()

            if isserver:
                info = CTakeDamageInfo(owner, owner, self.AttackPrimary.damage, DMG_CLUB)
                info.attributes = self.primaryattackattributes

                #if owner and pHitEntity.IsNPC():
                    # If bonking an NPC, adjust damage.
                #    info.AdjustPlayerDamageInflictedForSkillLevel()
                

                CalculateMeleeDamageForce(info, hitDirection, traceHit.endpos)

                pHitEntity.DispatchTraceAttack(info, hitDirection, traceHit) 
                ApplyMultiDamage()

                # Now hit all triggers along the ray that... 
                self.TraceAttackToTriggers(info, traceHit.startpos, traceHit.endpos, hitDirection)

            self.WeaponSound(MELEE_HIT)

        # Apply an impact effect
        self.ImpactEffect(traceHit)

    def ChooseIntersectionPointAndActivity(self, hitTrace, mins, maxs, pOwner):
        minmaxs = [mins, maxs]
        tmpTrace = trace_t()
        vecHullEnd = Vector(hitTrace.endpos)
        vecEnd = Vector()

        distance = 1e6
        vecSrc = hitTrace.startpos

        vecHullEnd = vecSrc + ((vecHullEnd - vecSrc)*2)
        UTIL_TraceLine(vecSrc, vecHullEnd, MASK_SHOT_HULL, pOwner, COLLISION_GROUP_NONE, tmpTrace)
        if tmpTrace.fraction == 1.0:
            for i in range(0, 2):
                for j in range(0, 2):
                    for k in range(0, 2):
                        vecEnd.x = vecHullEnd.x + minmaxs[i][0]
                        vecEnd.y = vecHullEnd.y + minmaxs[j][1]
                        vecEnd.z = vecHullEnd.z + minmaxs[k][2]

                        UTIL_TraceLine(vecSrc, vecEnd, MASK_SHOT_HULL, pOwner, COLLISION_GROUP_NONE, tmpTrace)
                        if tmpTrace.fraction < 1.0:
                            thisDistance = (tmpTrace.endpos - vecSrc).Length()
                            if thisDistance < distance:
                                hitTrace = tmpTrace
                                distance = thisDistance
        else:
            hitTrace = tmpTrace

        return ACT_VM_HITCENTER

    def ImpactWater(self, start, end):
        #FIXME: This doesn't handle the case of trying to splash while being underwater, but that's not going to look good
        #		 right now anyway...
        
        # We must start outside the water
        if UTIL_PointContents(start, MASK_ALL) & (CONTENTS_WATER|CONTENTS_SLIME):
            return False

        # We must end inside of water
        if not (UTIL_PointContents(end, MASK_ALL) & (CONTENTS_WATER|CONTENTS_SLIME)):
            return False

        waterTrace = trace_t()

        UTIL_TraceLine(start, end, (CONTENTS_WATER|CONTENTS_SLIME), self.GetOwner(), COLLISION_GROUP_NONE, waterTrace)

        if waterTrace.fraction < 1.0:
            #if isserver: ?
            data = CEffectData()

            data.flags  = 0
            data.origin = waterTrace.endpos
            data.normal = waterTrace.plane.normal
            data.scale = 8.0

            # See if we hit slime
            if waterTrace.contents & CONTENTS_SLIME:
                data.flags |= FX_WATER_IN_SLIME
            

            DispatchEffect( "watersplash", data )
        

        return True

    def ImpactEffect(self, traceHit):
        # See if we hit water (we don't do the other impact effects in this case)
        if self.ImpactWater(traceHit.startpos, traceHit.endpos):
            return

        #FIXME: need new decals
        UTIL_ImpactTrace(traceHit, DMG_CLUB)
    
    def Swing(self, bIsSecondary):
        """ Starts the swing of the weapon and determines the animation 
            input:
            bIsSecondary - is this a secondary attack?
        """
        
        traceHit = trace_t()

        # Try a ray
        pOwner = self.GetOwner()
        if not pOwner:
            return

        swingStart, forward = self.GetShootOriginAndDirection()

        swingEnd = swingStart + forward * (self.AttackPrimary.maxrange + 32)
        UTIL_TraceLine(swingStart, swingEnd, MASK_SHOT_HULL, pOwner, COLLISION_GROUP_NONE, traceHit )
        nHitActivity = self.hitactivity

        if isserver:
            # Like bullets, bludgeon traces have to trace against triggers.
            triggerInfo = CTakeDamageInfo(self.GetOwner(), self.GetOwner(), self.AttackPrimary.damage, DMG_CLUB)
            self.TraceAttackToTriggers(triggerInfo, traceHit.startpos, traceHit.endpos, vec3_origin )

        if traceHit.fraction == 1.0:
        
            bludgeonHullRadius = 1.732 * self.BLUDGEON_HULL_DIM  # hull is +/- 16, so use cuberoot of 2 to determine how big the hull is from center to the corner point

            # Back off by hull "radius"
            swingEnd -= forward * bludgeonHullRadius

            UTIL_TraceHull(swingStart, swingEnd, self.bludgeonmins, self.bludgeonmaxs, MASK_SHOT_HULL, pOwner, COLLISION_GROUP_NONE, traceHit)
            if traceHit.fraction < 1.0 and traceHit.ent:
                vecToTarget = traceHit.ent.GetAbsOrigin() - swingStart
                VectorNormalize(vecToTarget)

                dot = vecToTarget.Dot(forward)

                # YWB:  Make sure they are sort of facing the guy at least...
                if dot < 0.70721:
                    # Force amiss
                    traceHit.fraction = 1.0
                else:
                    nHitActivity = self.ChooseIntersectionPointAndActivity(traceHit, self.bludgeonmins, self.bludgeonmaxs, pOwner)


        self.WeaponSound(SINGLE)

        # -------------------------
        #	Miss
        # -------------------------
        if traceHit.fraction == 1.0:
            nHitActivity = self.missactivity2 if bIsSecondary else self.missactivity1

            # We want to test the first swing again
            testEnd = swingStart + forward * self.AttackPrimary.maxrange
            
            # See if we happened to hit water
            self.ImpactWater( swingStart, testEnd )
        else:
            self.Hit( traceHit, nHitActivity )

        # Send the anim
        self.SendWeaponAnim(nHitActivity)

        #pOwner.SetAnimation(PLAYER_ATTACK1)
        #ToHL2MPPlayer(pOwner).DoAnimationEvent( PLAYERANIMEVENT_ATTACK_PRIMARY )


        #Setup our next attack times
        self.nextprimaryattack = gpGlobals.curtime + self.firerate
        self.nextsecondaryattack = gpGlobals.curtime + self.firerate
    
    hitactivity = ACT_VM_HITCENTER
    missactivity1 = ACT_VM_MISSCENTER
    missactivity2 = ACT_VM_MISSCENTER2