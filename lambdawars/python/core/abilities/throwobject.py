"""Ability for throwing objects (grenades, projectiles, etc).

Provides a targeted ability that allows units to throw objects at targets
or positions. Handles range checking, line of sight validation, and
trajectory calculation for thrown projectiles.
"""
from vmath import VectorNormalize, Vector, QAngle, vec3_origin, vec3_angle
from .target import AbilityTarget
from fields import FloatField, StringField, BooleanField, VectorField
from unit_helper import VecCheckThrowTolerance
from entities import FOWFLAG_HIDDEN, FOWFLAG_NOTRANSMIT
import random

if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_PrecacheOther, UTIL_PredictedPosition
    from core.units import BaseBehavior
        
    class ActionThrowObject(BaseBehavior.ActionAbility):
        """Action for executing throw object ability.
        
        Handles unit movement into range, facing the target, and executing
        the throw animation. Manages the throw timing and object creation.
        """
        def Update(self):
            """Update the throw action, checking range and facing requirements.
            
            Moves the unit into range if needed, ensures it's facing the target,
            then triggers the throw animation. Handles both animation event-based
            and delay-based throw timing.
            """
            outer = self.outer
            abi = self.order.ability
            throwrange = abi.throwrange
            
            target = abi.throwtarget if abi.throwtarget else abi.throwtargetpos
            
            # In range?
            if abi.throwtarget:
                dist = outer.EnemyDistance(abi.throwtarget)
            else:
                dist = (outer.GetAbsOrigin() - abi.throwtargetpos).Length2D()
            fnloscheck = outer.GrenadeInRangeLOSCheck if hasattr(outer, 'GrenadeInRangeLOSCheck') else None
            if fnloscheck:
                if dist > throwrange or not fnloscheck(self.order.position, abi.throwtarget):
                    return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into grenade throw range', target, maxrange=throwrange, fncustomloscheck=fnloscheck) 
            else:
                if dist > throwrange:
                    return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving into grenade throw range', target, maxrange=throwrange) 
                    
            # Facing?
            if not outer.FInAimCone(target, abi.facingminimum):
                return self.SuspendFor(self.behavior.ActionFaceTarget, 'Not facing target', target, abi.facingminimum)

            self.throwedobject = True
            self.changetoidleonlostorder = False
            abi.DoThrowAnimation(outer)
            abi.SetNotInterruptible()
            
            if abi.useanimationevent:
                return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Executing attack', self.outer.animstate.specificmainactivity)
            return self.SuspendFor(self.behavior.ActionWait, 'Executing attack', abi.throwdelay)
            
        def OnEnd(self):
            """Called when the throw action ends.
            
            Cleans up the throw ability reference and cancels the ability
            to ensure proper cleanup even if already completed.
            """
            super().OnEnd()
            
            self.outer.throwability = None
            
            # Noop in case already cancelled or completed, so just call to be sure
            self.order.ability.Cancel()

        def OnResume(self):
            """Called when the throw action resumes after being suspended.
            
            If the object was already thrown (animation completed), actually
            throws the object and removes the order. Otherwise resumes normal
            behavior.
            """
            self.changetoidleonlostorder = True
            if self.throwedobject:
                abi = self.order.ability
                outer = self.outer
                if not abi.useanimationevent:
                    abi.ThrowObject(outer)
                self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        throwedobject = False

class AbilityThrowObject(AbilityTarget):
    """ Generic ability for throwing objects.
    
        Base usage:
        - Set objectclsname to the desired entity class name to be spawned and throwed. Must be child class from CBaseGrenade.
        - Implement OnObjectThrowed to customize the spawned entity
        - Optional: Set useanimationevent to True and throwanimation to a custom animation. 
                    Then implement the animation event handler and manual spawn the grenade entity.
    """
    objectclsname = StringField(value='', helpstring='Class name of entity to be spawned and throwed.')
    facingminimum = FloatField(value=0.7, helpstring='The minimum cone it needs to be facing')
    throwrange = FloatField(value=800.0, helpstring='Minimum throw range')
    throwspeed = FloatField(value=700.0, helpstring='Speed of throw')
    throwanimation = StringField(value='ANIM_MELEE_ATTACK1')
    throw_anim_speed = FloatField(value=1)
    throwstartoffset = VectorField(value=vec3_origin)
    throwstartattachment = StringField(value='')

    predict_target_position = BooleanField(value=False)
    
    useanimationevent = BooleanField(value=False)
    throwdelay = FloatField(value=0.5)
    
    throwtarget = None

    thumble_through_air = BooleanField(value=True)
    
    if isserver:
        @classmethod           
        def Precache(info):
            super().Precache()
            
            UTIL_PrecacheOther(info.objectclsname)
    
        def DoAbility(self):
            """Execute the throw object ability.
            
            Handles cheat mode instant throws or queues throw orders for
            selected units. Validates resources and sets up throw targets.
            """
            data = self.mousedata
            
            if self.ischeat:
                playerpos = self.player.GetAbsOrigin() + self.player.GetCameraOffset() 
                vecShootDir = data.endpos - playerpos
                VectorNormalize(vecShootDir)
                throwobject = CreateEntityByName(self.objectclsname)
                throwobject.SetAbsOrigin(playerpos)
                throwobject.SetOwnerNumber(self.ownernumber)
                DispatchSpawn(throwobject)
                self.SetupObject(throwobject)
                throwobject.SetVelocity(vecShootDir * 10000.0, Vector(0, 0, 0))
                self.Completed()
                return

            pos = data.groundendpos
            target = data.ent
            self.throwtargetpos = pos
            if target and not target.IsWorld():
                self.throwtarget = target
            
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            for unit in self.units:
                if getattr(unit, '_throwabi_%s_asattack' % self.name, False):
                    self.DoThrowAnimation(unit)
                else:
                    unit.AbilityOrder(position=pos,
                                      target=target,
                                      ability=self)

        def DoThrowAnimation(self, unit):
            """Play the throw animation on a unit.
            
            Args:
                unit: Unit entity to play the animation on.
            """
            unit.throwability = self
            unit.DoAnimation(getattr(unit, self.throwanimation), data=round(self.throw_anim_speed * 255))
                        
        def SetupObject(self, throwobject):
            """Setup the thrown object after creation.
            
            Override this method to customize the thrown object's properties
            such as damage, owner, or other attributes.
            
            Args:
                throwobject: The entity that was thrown.
            """
            pass

        def GetTossStartAndEnd(self, unit):
            """Calculate the start and end positions for the throw.
            
            Determines the throw start position from unit attachment or center,
            and the end position from target entity or target position. Optionally
            predicts target movement if enabled.
            
            Args:
                unit: Unit performing the throw.
                
            Returns:
                tuple: (startpos, endpos) Vector positions for the throw.
            """
            if self.throwstartattachment:
                startpos = Vector()
                unit.GetAttachment(self.throwstartattachment, startpos)
            else:
                startpos = unit.WorldSpaceCenter()
            startpos += self.throwstartoffset

            if self.throwtarget:
                endpos = self.throwtarget.GetAbsOrigin()
                if self.predict_target_position:
                    UTIL_PredictedPosition(self.throwtarget, 0.5, endpos)
            else:
                endpos = self.throwtargetpos

            return startpos, endpos
            
        def ThrowObject(self, unit):
            """Execute the throw for a unit.
            
            Calculates throw trajectory, creates and tosses the object,
            then calls OnObjectThrowed for customization.
            
            Args:
                unit: Unit performing the throw.
            """
            startpos, endpos = self.GetTossStartAndEnd(unit)

            throwobj = self.TossObject(unit, startpos, endpos, unit.CalculateIgnoreOwnerCollisionGroup())

            if throwobj:
                self.OnObjectThrowed(unit, throwobj)
                self.Completed()
                throwobj.SetVelocity(throwobj.GetAbsVelocity(), Vector(0, 0, 0))
            
        def OnObjectThrowed(self, unit, throwobject):
            """Called after an object has been successfully thrown.
            
            Sets up the object, applies recharge time, and completes the ability.
            Override to add custom behavior after throwing.
            
            Args:
                unit: Unit that threw the object.
                throwobject: The entity that was thrown.
            """
            self.throwobject = throwobject
            self.SetupObject(throwobject)
            self.SetRecharge(unit)
            self.Completed()

        def InRangeLOSCheck(self, testpos, target=None):
            """Check if a throw trajectory is valid from the test position.
            
            Validates that a valid throw vector can be calculated from the
            unit's position to the target, ensuring the throw is possible.
            
            Args:
                testpos (Vector): Position to test from (unused, uses unit position).
                target: Target entity (unused, uses ability target).
                
            Returns:
                bool: True if a valid throw trajectory exists, False otherwise.
            """
            unit = self.unit
            startpos, endpos = self.GetTossStartAndEnd(unit)

            vecToss = self.GetTossVector(unit, startpos, endpos, unit.CalculateIgnoreOwnerCollisionGroup())
            if not vecToss:
                return False

            return True

        def GetTossVector(self, unit, startpos, targetpos, collisiongroup):
            """ Gets the toss vector from start to target pos. 
            
                Args:
                    unit (entity): unit doing the toss
                    startpos (Vector): Start position of toss (usually the hand position of the unit)
                    targetpos (Vector): End position of toss. Usually a bit above the ground
                    collisiongroup (int): Collision mask used for testing
            """
            if not unit:
                return None

            # Try the most direct route
            vecToss = VecCheckThrowTolerance(unit, startpos, targetpos, self.throwspeed, (10.0*12.0), collisiongroup)

            # If this failed then try a little faster (flattens the arc)
            if vecToss == vec3_origin:
                vecToss = VecCheckThrowTolerance(unit, startpos, targetpos, self.throwspeed * 1.5, (10.0*12.0),
                                                 collisiongroup)
                if vecToss == vec3_origin:
                    return None

            return vecToss
    
        def TossObject(self, unit, startpos, targetpos, collisiongroup):
            """ Tosses the object from start to target. May fail. 
            
                Args:
                    unit (entity): unit doing the toss
                    startpos (Vector): Start position of toss (usually the hand position of the unit)
                    targetpos (Vector): End position of toss. Usually a bit above the ground
                    collisiongroup (int): Collision mask used for testing

                Returns:
                    object (entity): 
            """
            if not unit:
                return None;

            # Try and spit at our target
            vecToss = self.GetTossVector(unit, startpos, targetpos, collisiongroup)
            if not vecToss:
                return None

            # Find what our vertical theta is to estimate the time we'll impact the ground
            #Vector vecToTarget = ( vTarget - vSpitPos );
            #VectorNormalize( vecToTarget );
            velocity = VectorNormalize(vecToss)
            #float flCosTheta = DotProduct( vecToTarget, vecToss );
            #float flTime = (vSpitPos-vTarget).Length2D() / ( flVelocity * flCosTheta );

            # Emit a sound where this is going to hit so that targets get a chance to act correctly
            #CSoundEnt.InsertSound( SOUND_DANGER, vTarget, (15*12), flTime, this );

            object = CreateEntityByName(self.objectclsname)
            if not object:
                return None
            object.SetAbsOrigin(startpos)
            object.SetAbsAngles(vec3_angle)
            object.SetOwnerNumber(unit.GetOwnerNumber())
            object.AddFOWFlags(FOWFLAG_HIDDEN | FOWFLAG_NOTRANSMIT)
            DispatchSpawn(object)
            object.SetThrower(unit)
            object.SetOwnerEntity(unit)

            object.SetAbsVelocity(vecToss * velocity);

            if self.thumble_through_air:
                # Tumble through the air
                object.SetLocalAngularVelocity(
                    QAngle(random.uniform(-250, -500),
                           random.uniform(-250, -500),
                           random.uniform(-250, -500)))
            return object

        behaviorgeneric_action = ActionThrowObject
