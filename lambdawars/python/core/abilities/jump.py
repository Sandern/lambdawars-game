""" A generic base for a jumping ability. """
import math
from .target import AbilityTarget
from ..util.locomotion import CalcJumpVelocityChecked
from vmath import vec3_origin, VectorNormalize, Vector
from srcbase import MASK_SOLID
from utils import UTIL_TraceHull, trace_t
from core.units import PlaceUnit
from core.util.units import UnitProjector
from navmesh import NavMeshGetPositionNearestNavArea
# import ndebugoverlay
import random

from fields import FloatField, StringField, BooleanField


class JumpHomingUnitProjector(UnitProjector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.result = {}

    def ExecuteUnitForPosition(self, unit, position):
        self.result[unit] = position


class JumpLOSTester(object):
    """ LOS tester for unit navigation code."""
    def __init__(self, ability, unit):
        super().__init__()

        self.ability = ability
        self.unit = unit
        self.targets = None

    def __call__(self, testpos, target=None):
        ability = self.ability

        if ability.jump_homing:
            # Store targets so they can be later references by AI again
            # This can fix some edge cases where calling FindValidHomingJump again no longer returns targets when it
            # actually performs the jump.
            self.targets = ability.FindValidHomingJump(self.unit, self.unit.GetAbsOrigin(), testpos)
            return bool(self.targets)
        return ability.CalculateJump(self.unit, self.unit.GetAbsOrigin(), testpos) != vec3_origin


if isserver:
    from core.units import BehaviorGeneric, BaseAction
    from unit_helper import GF_REQTARGETALIVE, GF_USETARGETDIST
    import ndebugoverlay
    
    class ActionJump(BaseAction):
        """ Velocity based version of jump. Velocity is applied to unit, and unit physics do the rest. """
        def Init(self, order, parent_action):
            super().Init()
            
            self.order = order
            self.parent_action = parent_action
            
        def OnStart(self):
            outer = self.outer
            order = self.order
            abi = order.ability
            
            outer.SetGravity(abi.jumpgravity)
            outer.SetGroundEntity(None)
            if abi.jumpstartsound:
                outer.EmitSound(abi.jumpstartsound)
            if abi.collision:
                outer.SetCollisionGroup(outer.CalculateIgnoreOwnerCollisionGroup())
            
            startpos = outer.GetAbsOrigin()
            targetpos = order.target.GetAbsOrigin() if order.target else order.position

            outer.aimoving = True
            vecToss = abi.CalculateJump(outer, startpos, targetpos)
            if vecToss == vec3_origin:
                abi = order.ability
                abi.Cancel()
                self.parent_action.changetoidleonlostorder = True
                order.Remove(dispatchevent=True)
                return self.Continue()
                
            # Ignore friction temporary so we don't need to reckon with the velocity (since we are still
            # at the ground at jump start)
            outer.locomotion.IgnoreFriction(1.0)
            outer.SetAbsVelocity(vecToss)
            return super().OnStart()
            
        def OnEnd(self):
            super().OnEnd()
            
            outer = self.outer
            outer.SetGravity(1)
            outer.aimoving = False
            
        def Update(self):
            outer = self.outer
            order = self.order
            if outer.GetGroundEntity() or (order.target and order.target in outer.mv.blockers):
                abi = order.ability
                abi.SetRecharge(self.outer)
                abi.Completed()
                self.parent_action.changetoidleonlostorder = True
                order.Remove(dispatchevent=True)

                if abi.collision:
                    outer.SetCollisionGroup(outer.CalculateOwnerCollisionGroup())
                abi.OnLanded(outer)
                
                # Might already have a new order, in which case above dispatchevent does nothing
                # In that case we end the action. Otherwise do nothing.
                # Code is not nice, but will do for now.
                return self.Done('Landed') if self.valid else self.Continue()

    class ActionJumpHoming(BaseAction):
        """ Fake "homing" based version of jump. Uses three points (start, middle, end) and just moves the unit along
            it at a certain speed. Advtange is being much more controllable.
        """
        def Init(self, order, parent_action, jump_los_tester):
            super().Init()

            self.order = order
            self.parent_action = parent_action
            self.jump_los_tester = jump_los_tester

        def OnStart(self):
            outer = self.outer
            order = self.order
            abi = order.ability

            outer.locomotionenabled = False

            #outer.SetGravity(abi.jumpgravity)
            outer.SetGroundEntity(None)
            if abi.jumpstartsound:
                outer.EmitSound(abi.jumpstartsound)

            self.startpos = outer.GetAbsOrigin()
            self.targetpos = order.target.GetAbsOrigin() if order.target else order.position
            if abi.homing_projector:
                self.targetpos = abi.homing_projector.result.get(outer, self.targetpos)

            self.targets = self.jump_los_tester.targets
            self.curdisttravel = (self.targets[0] - self.startpos).Length()

        def OnEnd(self):
            outer = self.outer

            outer.locomotionenabled = True

        def Update(self):
            outer = self.outer
            order = self.order
            abi = order.ability

            if self.targets:
                curtargetpos = self.targets[0]

                origin = outer.GetAbsOrigin()
                dir = curtargetpos - origin
                dist = VectorNormalize(dir)
                traveldist = 1250 * outer.think_freq
                if dist < traveldist and len(self.targets) < 2:
                    traveldist = dist
                self.curdisttravel -= traveldist
                outer.SetAbsOrigin(origin + (dir * traveldist))

                if (outer.GetAbsOrigin() - curtargetpos).Length() < 32.0 or self.curdisttravel <= 0:
                    self.targets.pop(0)
                    if self.targets:
                        self.curdisttravel = (self.targets[0] - self.startpos).Length()

            if not self.targets:
                # Ensure valid position
                PlaceUnit(outer, outer.GetAbsOrigin())

                abi.SetRecharge(outer)
                abi.Completed()

                self.parent_action.changetoidleonlostorder = True
                order.Remove(dispatchevent=True)

                abi.OnLanded(outer)

                # Might already have a new order, in which case above dispatchevent does nothing
                # In that case we end the action. Otherwise do nothing.
                # Code is not nice, but will do for now.
                return self.Done('Landed') if self.valid else self.Continue()

    class ActionPerformJump(BehaviorGeneric.ActionMoveInRangeAndFace):
        """ Responsible for moving into range, facing the right direction and executing the
            jump action.
        """
        def Init(self, order, parent_action):
            target = order.target if order.target else order.position
            self.order = order
            self.parent_action = parent_action
            self.jump_los_tester = JumpLOSTester(order.ability, self.outer)

            super().Init(target, self.order.ability.maxrange, goalflags=GF_REQTARGETALIVE | GF_USETARGETDIST,
                         fncustomloscheck=self.jump_los_tester)
            
            self.ability = order.ability
            
        def Update(self):
            if not self.target:
                self.ability.Cancel()
                return self.Done('Lost target')
            return super().Update()
            
        def OnInRangeAndFacing(self):
            ability = self.ability
            
            outer = self.outer
            if not ability.TakeEnergy(outer):
                ability.Cancel(cancelmsg='#Ability_NotEnoughEnergy')
                return self.Done('Canceled ability due lack of energy')
            
            ability.SetNotInterruptible()
            
            outer = self.outer
            self.parent_action.changetoidleonlostorder = False
            outer.DoAnimation(outer.AE_BEING_JUMP, data=round(ability.jump_start_anim_speed*255))

            if ability.jump_homing:
                return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Doing homing jump animation', None,
                                     ActionJumpHoming, self.order, self.parent_action, self.jump_los_tester)
            else:
                return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Doing jump animation', None,
                                     ActionJump, self.order, self.parent_action)

        order = None
        parent_action = None
        jump_los_tester = None
        ability = None

    class ActionDoPerformJump(BehaviorGeneric.ActionInterruptible, BehaviorGeneric.ActionAbility):
        """ Container action for jump ability. """
        def OnStart(self):
            return self.SuspendFor(ActionPerformJump, 'Doing jump', self.order, self)
            
        def OnResume(self):
            self.order.Remove(dispatchevent=False)
            return super().OnResume()
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.order.ability.stopped:
                self.order.ability.Cancel()


class AbilityJump(AbilityTarget):
    maxrange = FloatField(value=1000, helpstring='Max jumping range')
    jumpgravity = FloatField(value=1.0, helpstring='Modifies gravity during jump. Falls quicker, velocity is adjusted accordingly.')
    jumptolerance = FloatField(value=32.0, helpstring='Tolerance towards jump target')

    jump_start_anim_speed = FloatField(value=1.0, helpstring='Speed modifier of jump start animation')
    jumpstartsound = StringField(value='', helpstring='Sound script name of jump start sound')

    jump_homing = BooleanField(value=False, helpstring='Alternative non-velocity jump mode. More predictable result.')
    only_direct = BooleanField(value=False, helpstring='Ability can only be executed if unit can jump from current location.')
    only_navmesh = BooleanField(value=False, helpstring='Ability can only be targeted at possible nav mesh locations')
    collision = False
    homing_projector = None

    def CalculateHomingJumpPoints(self, unit, startpos, targetpos, height=64.0):
        """ Given a start position and end position, compute number of points along which to jump.
            Used when jump_homing is true.

            Args:
                unit (entity): Unit doing the jump
                startpos (Vector): Start position
                endpos (Vector): End position

            Kwargs:
                height (float): Height of jump

            Returns (list): points
        """
        return [
            startpos + ((targetpos - startpos) / 2.0) + Vector(0, 0, height),
            targetpos,
        ]

    def FindValidHomingJump(self, unit, startpos, targetpos):
        heights = [64.0, 192.0]

        for height in heights:
            points = self.CalculateHomingJumpPoints(unit, startpos, targetpos, height=height)

            hullmins = unit.CollisionProp().OBBMins()
            hullmaxs = unit.CollisionProp().OBBMaxs()

            prevpoint = startpos
            tr = trace_t()
            for i, point in enumerate(points):
                UTIL_TraceHull(prevpoint, point, hullmins, hullmaxs, MASK_SOLID, unit,
                               unit.CalculateIgnoreOwnerCollisionGroup(), tr)
                if i == len(points) - 1:
                    flNearness = (tr.endpos - point).LengthSqr()
                    #ndebugoverlay.Box(tr.endpos, -Vector(8, 8, 8), Vector(8, 8, 8), 255, 0, 0, 255, 2.0)
                    #ndebugoverlay.Box(point, -Vector(8, 8, 8), Vector(8, 8, 8), 0, 255, 0, 255, 2.0)
                    if tr.fraction == 1 or flNearness <= math.pow(self.jumptolerance + unit.CollisionProp().BoundingRadius(), 2):
                        return points
                    #else:
                        #ndebugoverlay.SweptBox(prevpoint, point, hullmins, hullmaxs, unit.GetAbsAngles(), 255, 0, 0, 255, 2.0)
                        #print('Not close enough to end point %f > %f' %
                        #      (flNearness, math.pow(self.jumptolerance + unit.CollisionProp().BoundingRadius(), 2)))
                else:
                    if tr.fraction != 1.0:
                        break

                prevpoint = point
        return None

    def CalculateJump(self, unit, startpos, targetpos):
        """ Given a start position and end position, compute the jump vector.

            Args:
                unit (entity): Unit doing the jump
                startpos (Vector): Start position
                endpos (Vector): End position

            Returns (Vector): the jump vector (direction and speed). vec3_origin for failure.
        """
        jumpvel = CalcJumpVelocityChecked(unit, startpos, targetpos, 750.0, self.jumptolerance,
                                          unit.CalculateIgnoreOwnerCollisionGroup())
        if jumpvel == vec3_origin:
            jumpvel = CalcJumpVelocityChecked(unit, startpos, targetpos, 400.0, self.jumptolerance,
                                              unit.CalculateIgnoreOwnerCollisionGroup())
        return jumpvel

    def DoAbility(self):
        data = self.mousedata

        position = data.endpos
        target = data.ent if (data.ent and not data.ent.IsWorld()) else None
        if self.only_navmesh == True:
            adjustedtargetpos = NavMeshGetPositionNearestNavArea(position, beneathlimit=2048.0)
            if adjustedtargetpos != vec3_origin:
                position = adjustedtargetpos
        elif self.only_navmesh == False:
            pass


        if target and target not in self.units:
            position = target.GetAbsOrigin()+Vector(random.uniform(-100, 100), random.uniform(-100, 100), 0)

        if self.only_direct:
            # Collect units which can make the jump
            units = []
            out_of_range = False
            for unit in self.units:
                if (unit.GetAbsOrigin() - position).Length2D() > self.maxrange:
                    out_of_range = True
                    continue

                if not JumpLOSTester(self, unit)(position):
                    continue

                units.append(unit)

            # If not units, show error message
            if not units:
                if isserver:
                    if out_of_range:
                        self.Cancel(cancelmsg='#Ability_OutOfRange',
                                    debugmsg='Cannot jump to target position from current position')
                    else:
                        self.Cancel(cancelmsg='#Ability_InvalidPosition',
                                    debugmsg='Cannot jump to target position from current position')
                return

            # Collect positions around target position. Only for direct right now, otherwise might not make sense
            self.homing_projector = JumpHomingUnitProjector(position, units)
            self.homing_projector.Execute()
        else:
            units = self.units

        # Order them
        self.AbilityOrderUnits(units, ability=self, position=position, target=target)
        
    def OnLanded(self, unit):
        pass
        
    if isserver:
        behaviorgeneric_action = ActionDoPerformJump


class AbilityJumpGroup(AbilityJump):
    def SelectUnits(self):
        return self.SelectGroupUnits()
