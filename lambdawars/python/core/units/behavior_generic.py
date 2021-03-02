from srcbase import FL_FLY, MASK_NPCSOLID
from vmath import vec3_origin, Vector, QAngle, VectorAngles, AngleDiff, VectorNormalize
import random
from .intention import BaseBehavior, BaseAction
from unit_helper import UnitBasePath, GF_NOCLEAR, GF_REQTARGETALIVE, GF_USETARGETDIST, GF_OWNERISTARGET, GF_NOLOSREQUIRED, GF_ATGOAL_RELAX
from entities import Activity, MouseTraceData, D_HT, ACT_INVALID
from core.units.orders import coverspotsearchradiushover
from utils import UTIL_DropToFloor
import ndebugoverlay
from _recast import RecastMgr
from navmesh import NavMeshGetPositionNearestNavArea

class BehaviorGeneric(BaseBehavior):
    """ Defines a single behavior that covers moving and attacking. """
    class ActionIdle(BaseBehavior.ActionInterruptible, BaseAction):
        """ Idle action of the unit. The unit starts with this action.

            The idle action will listen to events like new orders and new enemies.
        """
        def Init(self, updateidleposition=True):
            super().Init()
            self.updateidleposition = updateidleposition

        def OnStart(self):
            """ Starts the idle action. Checks for orders and enemies. """
            outer = self.outer
            if self.updateidleposition:
                outer.lastidleposition = outer.GetAbsOrigin()
                self.updateidleposition = False

            # Make sure to die if we were previously in an action that didn't handle being killed.
            if not outer.IsAlive():
                return self.ChangeTo(self.behavior.ActionDie, 'we should be dead')

            # Check for an order transition
            trans = self.CheckOrders()
            if trans:
                return trans

            # Check autocast. This might result in an event and transition to a different action
            if outer.CheckAutoCast(outer.checkautocastonidle) and not self.valid:
                return self.Continue()

            # Default to checking enemy as last
            return self.CheckEnemy(outer.enemy)

        def Update(self):
            """ Checks if we moved too far away from our last ordered position.
                In that case move back."""
            # Moved away too much from our idle position?
            outer = self.outer
            if self.nexttoidleposition < gpGlobals.curtime:
                lastidleposition = outer.lastidleposition
                origin = outer.GetAbsOrigin()
                if (lastidleposition - origin).Length2D() > 256.0:
                    hidespot = outer.FindCoverSpot(lastidleposition, searchradius=coverspotsearchradiushover) if outer.cantakecover else None
                    if hidespot:
                        return self.SuspendFor(self.behavior.ActionMoveToIdlePosition, "Return to position", hidespot[1], tolerance=64.0, hidespot=hidespot)
                    else:
                        clampedidlepos = NavMeshGetPositionNearestNavArea(lastidleposition, unit=outer)
                        return self.SuspendFor(self.behavior.ActionMoveToIdlePosition, "Return to position", clampedidlepos if clampedidlepos != vec3_origin else lastidleposition, tolerance=64.0)
                self.nexttoidleposition = gpGlobals.curtime + 1.0
            return self.Continue()

        def OnResume(self):
            """ Called when the idle action resumes.

                Will store the current position if specified.
                Also checks for orders and enemies.
            """
            outer = self.outer
            if self.updateidleposition:
                outer.lastidleposition = outer.GetAbsOrigin()
                self.updateidleposition = False
            else:
                self.nexttoidleposition = 0 # Directly return to idle position

            # Check for an order transition
            trans = self.CheckOrders()
            if trans:
                return trans

            # Check autocast. This might result in an event and transition to a different action
            if outer.CheckAutoCast(outer.checkautocastonidle) and not self.valid:
                return self.Continue()

            # Default to checking enemy as last
            return self.CheckEnemy(outer.enemy)

        def DoOrder(self, o):
            """ Processes an order and changes to appropriate action."""
            if o.type == o.ORDER_MOVE:
                self.updateidleposition = True
                return self.SuspendFor(self.behavior.ActionOrderMove, 'Move order received', o)
            elif o.type == o.ORDER_ENEMY:
                if o.target:
                    if not self.outer.attacks:
                        # Change to a generic move order
                        o.type = o.ORDER_MOVE
                        self.updateidleposition = True
                        return self.SuspendFor(self.behavior.ActionOrderMove, 'Move order received', o)
                    self.outer.enemy = o.target
                    self.updateidleposition = True
                    return self.SuspendFor(self.behavior.ActionOrderAttack, 'Attack order received', o)
                # The enemy went None before we got the chance to attack it. Clear the order.
                o.Remove()
            elif o.type == o.ORDER_ABILITY:
                ability = o.ability
                action = getattr(ability, '%s_action' % self.behavior.name, None)
                if action:
                    return self.ChangeTo(action, 'Ability order received', o)
            else:
                assert(0)

        def CheckOrders(self):
            """ Checks if we need to do an order. """
            if self.outer.orders:
                return self.DoOrder(self.outer.curorder)

        def CheckEnemy(self, enemy):
            """ Checks if we have an enemy. If that is the case suspend for the attack action. """
            if not enemy:
                return

            outer = self.outer
            dist = (outer.GetAbsOrigin() - outer.lastidleposition).Length2D()
            if dist > self.maxchasedist:
                return None

            if outer.CheckAutoCast(outer.checkautocastonenemy) and not self.valid:
                return self.Continue()

            if outer.attacks:
                return self.SuspendFor(self.behavior.ActionAttack, 'Got an enemy', enemy, maxmovedist=self.maxchasedist,
                                       waitmoveuntilunderattack=self.idlewaitmoveuntilunderattack)

        def OnNewOrder(self, order):
            """ Listens to the OnNewOrder event."""
            return self.DoOrder(order)

        def OnNewEnemy(self, enemy):
            """ Listens to the OnNewEnemy event."""
            if self.outer.orders:
                return self.Continue()
            return self.CheckEnemy(enemy)

        def OnAttackInfoUpdated(self):
            """ Event dispatched when the attack info is updated.
                Mainly used to attack the active enemy in case the unit
                switches from no attacks to having attacks (for example
                when turning cloak off."""
            outer = self.outer
            if not self.is_active_action or outer.orders:
                return self.Continue()
            if outer.enemy:
                return self.OnNewEnemy(outer.enemy)

        def OnStartClimb(self, climbheight, direction):
            """ Listens to the OnStartClimb event."""
            if self.outer.aiclimb:
                return self.ChangeTo(self.behavior.ActionStartClimbing, 'Starting climbing',
                    climbheight, direction)

        def OnRequestMoveAway(self, frompoint, distance):
            if self.outer.orders:
                return
            dir = (frompoint - self.outer.GetAbsOrigin())
            dir.z = 0.0
            self.updateidleposition = True
            return self.SuspendFor(self.behavior.ActionMoveAway, 'Moving away on request', -dir,
                (distance/self.outer.mv.maxspeed))

        def OnAutocastChanged(self, info):
            """ Event triggered on changed autocast setting on unit.
                Rechecks idle autocast list if not executing an order.
            """
            outer = self.outer
            if outer.orders:
                return
            outer.CheckAutoCast(outer.checkautocastonidle)

        updateidleposition = True
        nexttoidleposition = 0.0
        maxchasedist = 2048.0
        idlewaitmoveuntilunderattack = True # On sensing an enemy, don't chase by default in idle action

    class ActionDie(BaseAction):
        """ Executed when the unit cannot become a ragdoll or did not gib. Plays the die animation. """
        def OnStart(self):
            if self.outer.animstate.HasActivity(Activity.ACT_DIESIMPLE):
                self.outer.DoAnimation(self.outer.ANIM_DIE)
                self.timeout = gpGlobals.curtime + 5.0
                #return self.SuspendFor(self.behavior.ActionWaitForActivity, 'Waiting for die animation')
            else:
                self.outer.SetThink(self.outer.SUB_Remove, gpGlobals.curtime)

        def Update(self):
            super().Update()

            if self.timeout < gpGlobals.curtime:
                self.outer.SetThink(self.outer.SUB_Remove, gpGlobals.curtime)

        def OnResume(self):
            self.outer.SetThink(self.outer.SUB_Remove, gpGlobals.curtime)

        timeout = 0

    class ActionStunned(BaseAction):
        def OnStart(self):
            self.outer.stunned = True
            return super().OnStart()

        def OnEnd(self):
            self.outer.stunned = False
            super().OnEnd()

        def Update(self):
            if not self.outer.IsStatusEffectActive('stunned'):
                return self.ChangeTo(self.behavior.ActionIdle, 'Stunned no longer active, switching to idle action')

    class ActionMoveTo(BaseAction):
        """ Generic action to move to a target (position or entity).

            The action will return the transition "Done" on nav complete and failure.
            If the action is suspended, the path will be saved. On resume it will restore
            the saved path.
        """
        def Init(self, target, tolerance=0.0, goalflags=GF_REQTARGETALIVE|GF_USETARGETDIST, maxmovedist=0, pathcontext=None):
            """ Inialize method.

                Args:
                   target (Vector or entity): target of this action.

                Kwargs:
                   tolerance (float): tolerance used for deciding we reached an ok position for our goal.
                            however the unit will still try to get as close as possible.
                   goalflags (int): flags for this goal.
            """
            super().Init()

            self.tolerance = tolerance
            self.goalflags = goalflags
            self.maxmovedist = maxmovedist
            self.pathcontext = pathcontext

            if type(target) is Vector:
                self.targetorigin = target
            else:
                self.target = target

        @property
        def targetposition(self):
            return self.target.GetAbsOrigin() if self.target else self.targetorigin

        def OnStart(self):
            if not self.savedpath:
                if not self.target:
                    res = self.outer.navigator.SetGoal(self.targetorigin, self.tolerance, self.goalflags)
                else:
                    res = self.outer.navigator.SetGoalTarget(self.target, self.tolerance, self.goalflags)
                if not res:
                    return self.Done("Failed to find a path to the move target")
            else:
                self.outer.navigator.path = self.savedpath
            self.outer.navigator.path.maxmovedist = self.maxmovedist
            self.outer.navigator.path.pathcontext = self.pathcontext

        def OnEnd(self):
            super().OnEnd()
            self.outer.navigator.StopMoving()

        def OnSuspend(self):
            """ Suspended for an another action. Stop moving and save our path information"""
            self.savedpath = UnitBasePath(self.outer.navigator.path) # Copy and save path
            self.outer.navigator.StopMoving()
            return super().OnSuspend()

        def OnResume(self):
            """ The move action is resumed. Restored our path and continue moving. """
            self.outer.navigator.path = self.savedpath

        def OnNavComplete(self):
            return self.Done("NavComplete, moved to position")

        def OnNavFailed(self):
            return self.Done("NavFailed, lost target?")

        def GetDebugString(self):
            return 'flags: %d, tolerance: %f' % (self.goalflags, self.tolerance)

        target = None
        targetorigin = Vector(vec3_origin)
        savedpath = None


    class ActionMoveToIdlePosition(ActionMoveTo):
        def Init(self, idleposition, tolerance=64.0, hidespot=None, **kwargs):
            """ Inialize method.

                Args:
                   idleposition(Vector): Target idle position

                Kwargs:
                   tolerance (float): Tolerance used for deciding we reached an ok position for our goal.
                              however the unit will still try to get as close as possible.
                   hidespot (tuple): The order used for initializing the action.
            """
            super().Init(idleposition, tolerance=tolerance, **kwargs)

            self.hidespot = hidespot

        def OnStart(self):
            self.startedtime = gpGlobals.curtime

            hidespot = self.hidespot
            if hidespot:
                if self.outer.TakeCoverSpot(hidespot[0], hidespot[1]):
                    self.tolerance = 32.0
                else:
                    # For some reason this hiding spot was already taken
                    self.hidespot = None

            return super().OnStart()

        def OnEnd(self):
            hidespot = self.hidespot
            if hidespot:
                self.outer.FreeCoverSpot()
            return super().OnEnd()

        # Override OnNavComplete and OnNavFailed to clear the order.
        def OnNavComplete(self):
            hidespot = self.hidespot

            if not self.outer.orders:
                # Go in hidespot mode if we have one assigned
                if hidespot and (hidespot[0] == self.outer.hidingspotid or hidespot[0] not in self.outer.used_cover_spots):
                    return self.ChangeTo(self.behavior.ActionHideSpot, 'Found a hide spot', hidespot)

            return self.Done("NavComplete, moved to position")

        def OnNewEnemy(self, enemy):
            if gpGlobals.curtime - self.startedtime < 3.0:
                return self.Continue() # Eat event, don't want idle action to change actions because of this

        startedtime = 0.0
        hidespot = None

    class ActionMoveInRange(ActionMoveTo):
        """ Generic action to move in range of a target (position or entity).

            Behaves the same way as ActionMoveTo.
        """
        def Init(self, target, maxrange, minrange=0.0, tolerance=0.0, goalflags=GF_REQTARGETALIVE|GF_USETARGETDIST,
                 maxmovedist=0, fncustomloscheck=None, pathcontext=None):
            """ Initialise method.

                Args:
                   target (Vector or entity): target of this action.
                   maxrange (float): Max range the goal is valid.

                Kwargs:
                   minrange (float): Min range the goal is valid.
                   tolerance (float): tolerance used for deciding we reached an ok position for our goal.
                             however the unit will still try to get as close as possible.
                   goalflags (int): flags for this goal.
                   maxmovedist (float):
                   fncustomloscheck (object): method to call for los checking
                   pathcontext (object): anything, can be used as reference for path
            """
            super().Init(target, tolerance, goalflags, maxmovedist, pathcontext=pathcontext)
            self.minrange = minrange
            self.maxrange = maxrange
            self.fncustomloscheck = fncustomloscheck

        def OnStart(self):
            if not self.target:
                res = self.outer.navigator.SetGoalInRange(self.targetorigin, self.maxrange, self.minrange,
                                                          goaltolerance=self.tolerance, goalflags=self.goalflags)
            else:
                res = self.outer.navigator.SetGoalTargetInRange(self.target, self.maxrange, self.minrange,
                                                                goaltolerance=self.tolerance, goalflags=self.goalflags)
            if not res:
                return self.Done("Failed to find a path to the move target")
            path = self.outer.navigator.path
            path.maxmovedist = self.maxmovedist
            path.fncustomloscheck = self.fncustomloscheck
            path.pathcontext = self.pathcontext

        fncustomloscheck = None

    class ActionWaitForActivityPassive(BaseBehavior.ActionWaitForActivity):
        """ Waits for activity and disables various event generating actions such
            as enemy changes. These could otherwise break the animation, as parent
            actions may be listening to these events. """
        orders_changed = False
        ending = False

        def OnStart(self):
            outer = self.outer
            outer.disable_update_active_enemy = True # No OnNewEnemy and OnLostEnemy events
            return super().OnStart()
        def OnEnd(self):
            super().OnEnd()

            outer = self.outer
            outer.disable_update_active_enemy = False

        def EndSpecificActivity(self):
            self.ending = True
            if self.orders_changed:
                outer = self.outer
                if len(outer.orders) > 0:
                    outer.DispatchEvent(outer.OnNewOrder, outer.curorder)
                else:
                    outer.DispatchEvent(outer.OnAllOrdersCleared)
                # In case above events leaded to a new transition, we should not return a transition
                # from here.
                if not self.valid:
                    return
            return super().EndSpecificActivity()

        def OnNewOrder(self, order):
            if self.ending:
                return # No longer eat event, fall through to parent actions
            self.orders_changed = True
            return self.Continue() # Eat event
        def OnAllOrdersCleared(self):
            if self.ending:
                return # No longer eat event, fall through to parent actions
            self.orders_changed = True
            return self.Continue() # Eat event

    class ActionAttackSharedNotActive(object):
        """ Base code for actions with attack code that do not use
            the attack target as the active navigation goal
            (use ActionAttack in this case)."""
        def CheckAttacks(self):
            outer = self.outer
            enemy = self.enemy
            if not enemy:
                return self.Continue()

            dist = outer.EnemyDistance(enemy)

            # Might need to wait
            if outer.nextattacktime > gpGlobals.curtime:
                return self.Continue()

            # Start facing enemy as soon as in sensing range
            if dist < outer.senses.sensedistance:
                if outer.navigator.facingtarget != enemy:
                    outer.navigator.facingtarget = enemy
                    outer.navigator.facingcone = outer.minattackcone
            else:
                outer.navigator.facingtarget = None

            # In range?
            if dist > self.attackrange:
                return self.Continue()

            # Test if facing the enemy properly
            if not outer.FInAimCone(enemy, outer.minattackcone):
                return self.Continue()

            # Find an attack we can do
            for attack in outer.attacks:
                if attack.requiresmovement or dist > attack.maxrange or not outer.FInAimCone(enemy, attack.cone) or not attack.CanAttack(enemy):
                    continue
                ret = attack.Attack(enemy, self)
                if type(ret) == bool:
                    if ret:
                        return self.SuspendFor(self.behavior.ActionWaitForActivityPassive, 'Waiting for attack animation', outer.animstate.specificmainactivity)
                    return self.Continue()
                return ret
            return self.Continue()

        def OnEnd(self):
            super().OnEnd()

            # Make sure we are no longer facing the enemy
            self.outer.navigator.facingtarget = None

        # Weapon related events
        def OnBurstFinished(self):
            activeweapon = self.outer.activeweapon
            # Must have a weapon, otherwise this event makes no sense
            if not activeweapon:
                return
            # Rest according to the burst settings
            self.outer.nextattacktime = gpGlobals.curtime + random.uniform(activeweapon.minresttime, activeweapon.maxresttime)
            return self.Continue()

        def OnOutOfClip(self):
            """ Called when the active weapon clip has runned out of ammo. """
            return self.SuspendFor(self.behavior.ActionReload, 'Waiting for reload animation')

    class ActionOrderMove(ActionAttackSharedNotActive, ActionMoveTo):
        """ Action for a move order. Clears the order on nav complete and failure."""
        def Init(self, order, tolerance=320.0):
            """ Initialize method.

                Args:
                   order (Order): The order used for initializing the action.

                Kwargs:
                   tolerance (float): Tolerance used for deciding we reached an ok position for our goal.
                              however the unit will still try to get as close as possible.
            """
            self.order = order
            self.enemy = self.outer.enemy
            self.attackrange = self.outer.maxattackrange

            super().Init(
                (order.target if order.target else order.position), tolerance)

        def OnStart(self):
            hidespot = self.order.hidespot
            if hidespot:
                if self.outer.TakeCoverSpot(hidespot[0], hidespot[1]):
                    self.tolerance = 32.0
                else:
                    self.order.hidespot = None # For some reason this hiding spot was already taken

            transition = super().OnStart()

            self.UpdateGoalFlags()

            return transition

        def OnEnd(self):
            outer = self.outer
            order = self.order

            # Ensure order is cleaned up when ending this action
            if outer.curorder == order:
                order.Remove(dispatchevent=False, allowrepeat=False)

            hidespot = order.hidespot
            if hidespot:
                outer.FreeCoverSpot()
            return super().OnEnd()

        def Update(self):
            followtarget = self.order.target
            outer = self.outer
            enemy = outer.enemy
            if followtarget and followtarget.IsUnit():
                senses = getattr(followtarget, 'senses', None)
                if senses:
                    # If we are following a (friendly) unit, then suspend to attack the enemy
                    #isnearfollowtarget = followtarget.senses.HasOther(outer)
                    if enemy or followtarget.enemy:
                        return self.SuspendFor(self.behavior.ActionAttack, 'Got an enemy', enemy or followtarget.enemy)

            if not outer.canshootmove or not enemy:
                outer.navigator.facingtarget = None # Make sure we are not facing the enemy anymore
                return self.Continue()
            return self.CheckAttacks()

        def UpdateGoalFlags(self):
            outer = self.outer
            followtarget = self.order.target
            if not followtarget or getattr(followtarget, 'isbuilding', False):
                return

            path = outer.navigator.path
            if len(outer.orders) > 1 and path:
                path.goalflags &= ~(GF_NOCLEAR|GF_ATGOAL_RELAX)
            else:
                path.goalflags |= (GF_NOCLEAR|GF_ATGOAL_RELAX)

        def OnOrderQueued(self, order):
            self.UpdateGoalFlags()

        # Override OnNavComplete and OnNavFailed to clear the order.
        def OnNavComplete(self):
            hidespot = self.order.hidespot
            outer = self.outer

            self.order.Remove(dispatchevent=False, allowrepeat=True)

            # Only if we have no further orders:
            if not outer.orders:
                # Go in hidespot mode if we have one assigned
                if hidespot and (hidespot[0] == outer.hidingspotid or hidespot[0] not in outer.used_cover_spots):
                    return self.ChangeTo(self.behavior.ActionHideSpot, 'Found a hide spot', hidespot)

            if self.order.angle and (not outer.orders or self.order.force_face_angle):
                return self.ChangeTo(self.behavior.ActionFaceYaw, 'NavComplete, now facing order angle', self.order.angle.y)
            return self.Done("NavComplete, moved to position")

        def OnNavFailed(self):
            self.order.Remove(dispatchevent=False)
            return self.Done("NavFailed, lost target?")

        def OnNewEnemy(self, enemy):
            self.enemy = enemy

            # If we are following a (friendly) unit, then suspend to attack the enemy
            followtarget = self.order.target
            if followtarget and followtarget.IsUnit() and followtarget.enemy:
                return self.SuspendFor(self.behavior.ActionAttack, 'Got an enemy', enemy)

            return self.Continue()

        def OnEnemyLost(self):
            self.enemy = None
            return self.Continue()

    class ActionAttackNoMovement(ActionAttackSharedNotActive, BaseAction):
        """ The unit executing this action will try to attack the enemy when
            in range. However the unit will not attempt to move closer (regardless of
            whether the unit is capable of doing so).
        """
        def Init(self, enemy):
            """ Initialize method.

                Args:
                   enemy (entity): The entity we want to attack.
            """
            super().Init()
            self.enemy = enemy
            self.attackrange = self.outer.maxattackrange

        def Update(self):
            if not self.outer.IsValidEnemy(self.enemy):
                return self.Done('Lost enemy')
            return self.CheckAttacks()

        def OnAttackInfoUpdated(self):
            # Just need to store the updated max attack range...
            self.attackrange = self.outer.maxattackrange


    class ActionAttack(ActionMoveInRange):
        """ The unit executing this action will try to attack the enemy when
            in range. It will also try to move into range when it's not in range yet.
        """
        def Init(self, enemy, goalflags=GF_NOCLEAR|GF_REQTARGETALIVE|GF_USETARGETDIST, forcedenemy=False, maxmovedist=0,
                 waitmoveuntilunderattack=False):
            """ Inialize method.

                Args:
                   enemy (entity): The entity we want to attack.

                Kwargs:
                   goalflags (int): flags
                   forcedenemy (bool): force to keep this enemy. If not True the unit enemy selection might
                                       override the current enemy (and invalidate this action).
            """
            self.enemy = enemy.GetHandle()
            self.attackrange = self.outer.maxattackrange
            self.forcedenemy = forcedenemy
            self.waitmoveuntilunderattack = waitmoveuntilunderattack
            super().Init(enemy, self.attackrange,
                    self.outer.minattackrange, 0.0, goalflags, maxmovedist)

        def OnStart(self):
            outer = self.outer
            if not outer.attacks:
                return self.Done('No attacks...')
            if self.forcedenemy:
                outer.forcedenemy = True
            trans = super().OnStart()
            if self.waitmoveuntilunderattack:
                outer.navigator.nopathvelocity = True
            return trans

        def OnEnd(self):
            super().OnEnd()
            outer = self.outer
            outer.navigator.facingtarget = None
            if self.forcedenemy:
                outer.forcedenemy = False
            self.ClearWaitMoveUntilUnderAttack()

        def ClearWaitMoveUntilUnderAttack(self):
            if not self.waitmoveuntilunderattack:
                return
            self.outer.navigator.nopathvelocity = False
            self.waitmoveuntilunderattack = False

        def Update(self):
            outer = self.outer
            enemy = self.enemy

            if not outer.IsValidEnemy(enemy, require_alive=self.goalflags & GF_REQTARGETALIVE):
                return self.Done('Lost enemy')

            # Get last computed goal distance from our navigator (same as using EnemyDistance)
            dist = self.outer.navigator.GetGoalDistance()

            # Might be waiting until moving closer until we are under attack or until we have LOS
            if self.waitmoveuntilunderattack:
                engagedistance = outer.engagedistance
                beingattacked = (gpGlobals.curtime - outer.lasttakedamage) < 2.0
                nearestfriend = outer.senses.GetNearestAttackedFriendly()
                if nearestfriend and hasattr(nearestfriend, 'lasttakedamage'):
                    friendattacked = (gpGlobals.curtime - nearestfriend.lasttakedamage) < 2.0
                else:
                    friendattacked = False
                if hasattr(enemy, 'lasttakedamage'):
                    enemyattacked = (gpGlobals.curtime - enemy.lasttakedamage) < 2.0
                else:
                    enemyattacked = False
                if self.atgoal or beingattacked or enemyattacked or friendattacked or (dist <= engagedistance and outer.FastLOSCheck(enemy.BodyTarget(outer.GetAbsOrigin(), False))):
                    self.ClearWaitMoveUntilUnderAttack()

            # Update attack range if we have more than one attack
            if len(outer.attacks) > 1:
                self.outer.UpdateAttackInfo()
                self.outer.navigator.UpdateGoalInRange(self.outer.maxattackrange)

            # Wait for events
            if not self.atgoal:
                return self.Continue()

            if self.forcedenemy and not enemy:
                return self.Done('Lost enemy (enemy None)')

            # Might need to wait
            if outer.nextattacktime > gpGlobals.curtime:
                return self.Continue()

            # Find an attack we can do
            for attack in outer.attacks:
                if dist > attack.maxrange or not outer.FInAimCone(enemy, attack.cone) or not attack.CanAttack(enemy):
                    continue
                ret = attack.Attack(enemy, self)
                if type(ret) == bool:
                    if ret:
                        return self.SuspendFor(self.behavior.ActionWaitForActivityPassive, 'Waiting for attack animation',
                                               self.outer.animstate.specificmainactivity)
                    return self.Continue()
                return ret

            return self.Continue()

        def OnAttackInfoUpdated(self):
            # Just need to store the updated max attack range...
            self.attackrange = self.outer.maxattackrange

        def OnFacingTarget(self):
            self.isfacingtarget = True

        def OnLostFacingTarget(self):
            self.isfacingtarget = False

        def OnNavAtGoal(self):
            self.atgoal = True
            self.outer.navigator.facingtarget = self.enemy
            self.outer.navigator.facingcone = self.outer.minattackcone

        def OnNavLostGoal(self):
            self.atgoal = False
            self.outer.navigator.facingtarget = None

        def GetDebugString(self):
            return 'atgoal: %s, facingtarget: %s, %s' % (self.atgoal, self.isfacingtarget, super().GetDebugString())

        # Weapon related events
        def OnBurstFinished(self):
            activeweapon = self.outer.activeweapon
            assert activeweapon, 'expecting an active weapon in OnBurstFinished event' # Must have a weapon, otherwise this event makes no sense
            # Rest
            self.outer.nextattacktime = gpGlobals.curtime + random.uniform(activeweapon.minresttime, activeweapon.maxresttime)
            return self.Continue()

        def OnOutOfClip(self):
            """ Called when the active weapon clip has runned out of ammo. """
            return self.SuspendFor(self.behavior.ActionReload, 'Waiting for reload animation')

        # Ignore NavComplete and NavFailed.
        # NavFailed is only called when the target dies, but is also
        # covered by OnEnemyLost.
        def OnNavComplete(self):
            return self.Continue()
        #def OnNavFailed(self):
        #    return self.Continue()

        onresumedone = False
        atgoal = False
        isfacingtarget = False
        waitmoveuntilunderattack = False # Wait moving to enemy until we are under attack

    class ActionOrderAttack(ActionAttack):
        """ Order version of the attack action.
            Clears the order when the enemy died.
        """
        def Init(self, order):
            """ Inialize method.

                Args:
                   order (Order): The order used for initializing the action.
            """
            super().Init(order.target, forcedenemy=True)
            self.order = order

        def OnEnd(self):
            self.order.Remove(dispatchevent=False)
            super().OnEnd()

    class ActionAttackMove(ActionMoveTo):
        """ The attack move action will make the unit move towards the goal position and
            eliminate (or die while trying) all enemies along the path."""
        def OnStart(self):
            transition = super().OnStart()
            if self.outer.enemy:
                return self.OnNewEnemy(self.outer.enemy)
            return transition

        def Update(self):
            # Check if target can still be seen. Note that we might be moving to a position, in which
            # case target is not set.
            if self.target and not self.outer.IsValidEnemy(self.target, require_alive=False):
                return self.Done('Lost target (no longer valid enemy)')
            return super().Update()

        def OnNewEnemy(self, enemy):
            if enemy.IsAlive():
                return self.SuspendFor(self.behavior.ActionAttack, 'New enemy', enemy)
            else:
                return self.SuspendFor(self.behavior.ActionAttack, 'New enemy (not alive)', enemy, goalflags=GF_NOCLEAR|GF_USETARGETDIST)

    class ActionOrderAttackMove(ActionAttackMove):
        """ Same as ActionAttackMove, but is done on resume when the current order is
            different from the provided one. """
        def Init(self, order, *args, **kwargs):
            super().Init(*args, **kwargs)
            self.order = order

        def OnEnd(self):
            super().OnEnd()

            # Something canceled this action. Make sure we are no longer doing this order, otherwise action idle might
            # start this action again
            if self.outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)

        def OnResume(self):
            if self.outer.curorder != self.order:
                return self.Done('Action done, order changed.')
            return super().OnResume()

        def OnNavComplete(self):
            self.order.Remove(dispatchevent=False, allowrepeat=True)
            
            return super().OnNavComplete()

    class ActionAbilityAttackMove(BaseBehavior.ActionInterruptible, BaseBehavior.ActionAbility):
        def OnStart(self):
            target = self.order.target
            if target and not target.IsWorld() and (not target.IsUnit() or target.CanBeSeen()):
                # Check if we hate the target. If not, ensure it by adding an entity relationship
                if self.outer.IRelationType(target) != D_HT:
                    self.htrelapplied = True
                    self.outer.AddEntityRelationship(target, D_HT, 10)
                    self.outer.senses.ForcePerformSensing()
                    self.outer.UpdateEnemy(self.outer.senses) # Extra check
                goalflags = GF_REQTARGETALIVE if target.IsAlive() else 0
                return self.SuspendFor(self.behavior.ActionOrderAttackMove, "Attack move target", self.order, target, tolerance=32.0, goalflags=goalflags)
            return self.SuspendFor(self.behavior.ActionOrderAttackMove, "Attack move position", self.order, self.order.position, tolerance=32.0, goalflags=0)

        def OnResume(self):
            # When this order is resumed it reached the target/position
            # In that case clear the ability order. This will generate an event
            # that changes back to the idle action.
            if self.outer.curorder == self.order:
                self.order.Remove(allowrepeat=True)
            else:
                return super().OnResume()

        def OnEnd(self):
            if self.htrelapplied:
                self.outer.RemoveEntityRelationship(self.order.target)

        htrelapplied = False

    class ActionHoldPosition(BaseBehavior.ActionInterruptible, BaseBehavior.ActionAbility):
        def OnStart(self):
            outer = self.outer
            if len(outer.orders) > 1:
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Order queued, continue with next order')

            # Take movement control
            outer.navigator.StopMoving()
            outer.aimoving = True
            outer.mv.Clear()
            if outer.enemy:
                return self.OnNewEnemy(outer.enemy)

        def OnEnd(self):
            # Give back movement control to locomotion component
            self.outer.aimoving = False

        def OnNewEnemy(self, enemy):
            return self.SuspendFor(self.behavior.ActionAttackNoMovement, 'Enemy, lock on.', enemy)
        def OnEnemyLost(self):
            return self.SuspendFor(self.behavior.ActionNoop, 'Lost enemy')

        def OnOrderQueued(self, order):
            self.order.Remove(dispatchevent=False)
            return self.ChangeToIdle('Order queued, continue with next order')

    class ActionAbilityWaitForAnimation(BaseBehavior.ActionInterruptible, BaseBehavior.ActionWaitForActivity):
        """ Waits for animation as part of abilities derived from """

        def Init(self, order):
            """ Initialize method.

                Args:
                   order (Order): Instance of the ability order.
            """
            super().Init()
            self.order = order

        def SetupActivity(self):
            if not self.order.ability.TryStartAnimation(self.outer):
                return ACT_INVALID
            return super().SetupActivity()

        def OnStartInvalidActivity(self):
            return self.ChangeTo(self.behavior.ActionIdle, 'Invalid activity, order cleared')

        def OnEnd(self):
            super().OnEnd()

            if self.outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)

        def EndSpecificActivity(self):
            return self.ChangeTo(self.behavior.ActionIdle, 'Activity done or interrupted, order cleared')

    class ActionGarrisoned(BaseAction):
        def OnStart(self):
            # Take movement control
            self.outer.navigator.StopMoving()
            self.outer.aimoving = True
            if self.outer.enemy:
                return self.OnNewEnemy(self.outer.enemy)

        def OnEnd(self):
            # Give back movement control to locomotion component
            self.outer.aimoving = False

        def OnNewEnemy(self, enemy):
            return self.SuspendFor(self.behavior.ActionAttackNoMovement, 'Enemy, lock on.', enemy)

    class ActionHideSpotAttack(ActionAttackNoMovement):
        def Update(self):
            outer = self.outer
            enemy = self.enemy

            if enemy:
                # Did we receive damage?
                lastdamagetime = gpGlobals.curtime - outer.lasttakedamage
                if lastdamagetime < 1.0:
                    # Are we in range of our enemy (i.e. can we shoot it?)
                    dist = outer.EnemyDistance(enemy)
                    if dist > outer.maxattackrange:
                        # Not in attack range, but receiving damage
                        # Try to find a closer cover spot and move to it
                        origin = outer.GetAbsOrigin()
                        enemypos = enemy.GetAbsOrigin()
                        dir = enemypos - origin
                        VectorNormalize(dir)

                        boundsradius = outer.CollisionProp().BoundingRadius2D()
                        searchradius = (outer.maxattackrange / 2.0)
                        movedist = dist - outer.maxattackrange + boundsradius
                        testclosestpos = origin + (dir * movedist)
                        testpos = testclosestpos + (dir * searchradius)

                        coverspot = outer.FindCoverSpot(testpos, searchradius=searchradius, testclosestpos=testclosestpos)
                        if coverspot:
                            outer.MoveOrder(coverspot[1])
                            return self.Continue()

            return super().Update()

    class ActionCrouchHoldSpot(BaseAction):
        """ Hold position and crouch. Attack any nearby units. """
        def OnStart(self):
            # Take movement control
            outer = self.outer

            outer.lastidleposition = outer.GetAbsOrigin()
            outer.navigator.StopMoving()
            outer.aimoving = True
            outer.crouching = True

            if outer.enemy:
                return self.SuspendFor(self.behavior.ActionHideSpotAttack, 'Attacking enemy from cover/hold spot', outer.enemy)

        def OnEnd(self):
            # Give back movement control to locomotion component
            outer = self.outer
            outer.aimoving = False
            outer.crouching = False

            outer.DisableAsNavObstacle()

        def OnNewEnemy(self, enemy):
            return self.SuspendFor(self.behavior.ActionHideSpotAttack, 'Attacking enemy from cover/hold spot', enemy)

        def Update(self):
            if not self.addedobstacled:
                outer = self.outer
                if not outer.IsMoving():
                    self.addedobstacled = True
                    #ndebugoverlay.Box(outer.GetAbsOrigin(), -Vector(12, 12, 8), Vector(12, 12, 8), 0, 255, 0, 255, 5.0)
                    outer.EnableAsNavObstacle()
            return super().Update()

        addedobstacled = False

        '''def OnNewOrder(self, o):
            """ Processes an order and changes to appropriate action."""
            outer = self.outer
            if o.type == o.ORDER_ENEMY:
                target = o.target
                if target and target.GetAbsOrigin().DistToSqr(outer.GetAbsOrigin()) < outer.maxattackrange*outer.maxattackrange:
                    # Just change enemy for now when already in range and ignore the order
                    o.Remove(dispatchevent=False)
                    return self.SuspendFor(self.behavior.ActionAttackNoMovement, 'Enemy, lock on.', target)'''

    class ActionHideSpot(ActionCrouchHoldSpot):
        """ In addition to ActionCrouchHoldSpot, applies cover bonus. """
        def Init(self, hidespot):
            super().Init()
            self.hidespot = hidespot

        def OnStart(self):
            outer = self.outer
            if not outer.TakeCoverSpot(self.hidespot[0], self.hidespot[1]):
                return self.Done('Hiding spot already taken!')

            transition = super().OnStart()

            cover_info = outer.cover_spots_info.get(outer.hidingspotid, outer.default_cover_spot)
            outer.in_cover = cover_info.type
            outer.OnInCoverChanged()  # TODO: Add support for properties in fields (incover)

            return transition

        def OnEnd(self):
            super().OnEnd()

            # Free hide spot
            outer = self.outer
            outer.FreeCoverSpot(dispatch_event=False)
            outer.in_cover = 0
            outer.OnInCoverChanged()  # TODO: Add support for properties in fields (incover)

        def OnCoverSpotCleared(self):
            return self.Done('Cover spot was freed.')

    class ActionReload(BaseAction):
        """ Plays the reload action and waits for it. """
        def OnStart(self):
            outer = self.outer
            outer.DoAnimation(outer.ANIM_RELOAD_LOW if outer.crouching else outer.ANIM_RELOAD)
            return self.SuspendFor(self.behavior.ActionWaitForActivityPassive, 'Waiting for reload animation')

        def OnResume(self):
            return self.Done('Done reloading')

    class ActionFaceTarget(BaseAction):
        """ Generic action for facing a given target (position or entity) """
        def Init(self, target, facingcone=0.994):
            """ Initialize method.

                Args:
                   target (entity|vector): Move and face target (entity or position).

                Kwargs:
                   facingcone (float): Minimum facing cone target.
            """
            super().Init()

            self.target = target
            self.facingcone = facingcone

        def OnStart(self):
            if type(self.target) is Vector:
                self.outer.navigator.facingtargetpos = self.target
            else:
                self.outer.navigator.facingtarget = self.target
            self.outer.navigator.facingcone = self.facingcone

            return super().OnStart()

        def OnEnd(self):
            self.outer.navigator.facingtarget = None
            self.outer.navigator.facingtargetpos = vec3_origin

            super().OnEnd()

        def OnFacingTarget(self):
            return self.Done("Facing target")

    class ActionLockAim(ActionFaceTarget):
        """ Locks aim at target for a given duration. """
        def Init(self, target, facingcone=0.994, duration=1.0):
            super().Init(target, facingcone=facingcone)

            self.duration = duration

        def OnStart(self):
            self.endtime = gpGlobals.curtime + self.duration

            return super().OnStart()

        def Update(self):
            if self.endtime < gpGlobals.curtime:
                return self.Done("End locking target")

        def OnFacingTarget(self):
            pass # Do nothing on facing target

    class ActionFaceYaw(BaseAction):
        """ Generic action for facing a given absolute yaw.

            Calls OnFacingIdealYaw when it satisfies the ideal yaw.
            By default this methods returns the transition Done.
        """
        def Init(self, idealyaw, tolerance=2.5):
            """ Inialize method.

                Args:
                   idealyaw (float): The ideal yaw we try to achieve.

                Kwargs:
                   tolerance (float): Max allowed facing tolerance in degrees
            """
            super().Init()
            self.idealyaw = idealyaw
            self.tolerance = tolerance

        def OnStart(self):
            self.outer.navigator.idealyaw = self.idealyaw
            self.outer.navigator.idealyawtolerance = self.tolerance

        def OnEnd(self):
            self.outer.navigator.idealyaw = -1

        def OnFacingTarget(self):
            return self.Done("Facing ideal yaw")

    class ActionMoveInRangeAndFace(BaseAction):
        """ Generic action for moving in range and facing a target.

            The action will first try to move in range. Once in range it will
            face the target. Finally it calls OnInRangeAndFacing, which should
            return a transition (by default it returns Done).
        """
        def Init(self, target, maxrange=1024.0, facingcone=0.994, goalflags=GF_REQTARGETALIVE|GF_USETARGETDIST,
                 fncustomloscheck=None, pathcontext=None):
            """ Inialize method.

                Args:
                   target (entity): Move and face target (entity or position).

                Kwargs:
                   maxrange (float): Minimum range we should be in to fullfill the goal requirements.
                   facingcone (float): Minimum facing cone target
                   pathcontext (object): Optional path target
            """
            self.target = target
            self.maxrange = maxrange
            self.facingcone = facingcone
            self.goalflags = goalflags
            self.fncustomloscheck = fncustomloscheck
            self.pathcontext = pathcontext if pathcontext else self

        def Update(self):
            target = self.target
            outer = self.outer

            path = outer.navigator.path
            if path.pathcontext != self.pathcontext or not path.success:
                return self.SuspendFor(self.behavior.ActionMoveInRange, 'Not in range', target, self.maxrange, 0, 0.0,
                                       goalflags=self.goalflags, fncustomloscheck=self.fncustomloscheck,
                                       pathcontext=self.pathcontext)

            if not outer.FInAimCone(target, self.facingcone):
                return self.SuspendFor(self.behavior.ActionFaceTarget, 'Not facing target', target, self.facingcone)

            return self.OnInRangeAndFacing()

        def OnInRangeAndFacing(self):
            return self.Done('In range and facing')

    class ActionMoveAway(BaseAction):
        """ Move away in the given direction for a duration. """
        def Init(self, dir, duration=1.0):
            self.dir = dir
            self.duration = duration

        def OnStart(self):
            self.endtime = gpGlobals.curtime + self.duration
            self.outer.navigator.forcegoalvelocity = self.dir * self.outer.mv.maxspeed

        def OnEnd(self):
            self.outer.navigator.forcegoalvelocity.Invalidate()

        def Update(self):
            if gpGlobals.curtime > self.endtime:
                return self.Done('Duration expired')
            return self.Continue()

    class ActionConstruct(BaseBehavior.ActionInterruptible, BaseBehavior.ActionAbility):
        """ Generic construct action. """
        def OnStart(self):
            outer = self.outer
            if not self.order.target:
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Repair/construct target went None')

            if outer.constructweapon:
                if outer.activeweapon:
                    self.oldweapon = outer.activeweapon.GetClassname()
                outer.Weapon_Switch(outer.Weapon_OwnsThisType(outer.constructweapon))

            outer.navigator.facingtarget = self.order.target
            self.constructmaxrange = outer.constructmaxrange
            return super().OnStart()

        def Update(self):
            # When auto casted, new orders cancel us
            abi = self.order.ability
            autocasted = abi and abi.autocasted
            if autocasted and len(self.outer.orders) > 1:
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Canceling order because of a new order (auto casted)')

            # Check if target is valid and if we are in range
            target = self.order.target
            if not target or not target.IsAlive():
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Repair/construct target went None or not alive')
            dist = self.outer.EnemyDistance(target)
            if not self.isinrange and dist > self.constructmaxrange:
                self.movinginrange = True
                goalflags = GF_USETARGETDIST|GF_OWNERISTARGET
                if self.constructmaxrange < 64.0:
                    goalflags |= GF_NOLOSREQUIRED
                return self.SuspendFor(self.behavior.ActionMoveInRange, "Moving to spot (dist: %f)" % (dist), target, self.constructmaxrange, goalflags=goalflags)

            # Check if done
            if target.constructprogress >= 1.0:
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Repair/construct completed')

            # Do a construction step
            if not self.StartConstructing():
                return self.ChangeToIdle('Unit cannot construct or repair.')
            target.ConstructStep(self.outer.think_freq)
            return self.Continue() # Don't wait for activity

        def OnEnd(self):
            outer = self.outer
            if self.oldweapon:
                outer.Weapon_Switch(outer.Weapon_OwnsThisType(self.oldweapon))

            outer.navigator.facingtarget = None
            outer.aimoving = False
            self.StopConstructing()

        def OnResume(self):
            if self.movinginrange:
                if self.outer.navigator.path.success:
                    self.isinrange = True
                self.movinginrange = False
            return super().OnResume()

        def OnSuspend(self):
            self.StopConstructing() # Don't construct while suspended
            return super().OnSuspend()

        def StartConstructing(self):
            outer = self.outer
            if outer.constructing:
                return True
            target = self.order.target
            if target.isbuilding:
                if not target.NeedsUnitConstructing(unit=outer) and target.constructionstate in [target.BS_UNDERCONSTRUCTION, target.BS_UPGRADING]:
                    return False
            if target.health >= target.maxhealth:
                return False
            outer.constructing = True
            outer.aimoving = True

            target.constructors.add(outer.GetHandle())
            return True

        def StopConstructing(self):
            outer = self.outer
            if not outer.constructing:
                return
            outer.constructing = False
            outer.aimoving = False

            target = self.order.target
            if target:
                target.constructors.discard(outer.GetHandle())

        oldweapon = ''
        movinginrange = False
        isinrange = False

    class ActionRepair(ActionConstruct):
        """ Generic repair action. """
        def Update(self):
            abi = self.order.ability
            autocasted = abi and abi.autocasted

            target = self.order.target
            if not target or not target.IsAlive():
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Repair/construct target went None or is not alive')
            dist = self.outer.EnemyDistance(target)
            if not self.isinrange and dist > self.constructmaxrange:
                self.movinginrange = True
                goalflags = GF_USETARGETDIST|GF_OWNERISTARGET
                if self.constructmaxrange < 64.0: goalflags |= GF_NOLOSREQUIRED
                return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving to spot (dist: %f)' % (dist), target, self.constructmaxrange, goalflags=goalflags)

            if target.health >= target.maxhealth:
                self.order.Remove(dispatchevent=False)
                return self.ChangeToIdle('Repair/construct completed')

            if not self.StartConstructing():
                return self.ChangeToIdle('Unit cannot construct or repair.')
            target.RepairStep(self.outer.think_freq, self.outer.repairhpps)
            return self.Continue()

    class ActionPlaceObject(BaseBehavior.ActionInterruptible, BaseBehavior.ActionAbility):
        """ Core action for placing objects.

        """
        def OnStart(self):
            super().OnStart()

            # placemaxrange is related to the size of building and should be the distance to the edge of the place pos
            # (more or less). constructmaxrange determines the range at which the unit may start constructing.
            # Rebel Engineers must be at the edge, while Combine Stalkers have some distance.
            constructmaxrange = getattr(self.outer, 'constructmaxrange', 0)
            self.maxrange = self.order.ability.placemaxrange + constructmaxrange

        def Update(self):
            outer = self.outer
            order = self.order
            if outer.navigator.path.pathcontext != self or not outer.navigator.path.success:
                return self.SuspendFor(self.behavior.ActionMoveInRange, 'Moving to spot', order.target if order.target else order.position, self.maxrange, 0, 32.0, pathcontext=self)

            if not order.ability.IsValidPosition(order.position):
                order.ability.Cancel(cancelmsg='Failed to place building (invalid position)')
                order.Remove()
                return self.Continue()

            if self.placetimeout and self.placetimeout < gpGlobals.curtime:
                order.ability.Cancel(cancelmsg='Failed to place building (blocked)')
                order.Remove()
                return self.Continue()

            tellmoveaway = order.ability.tellmoveaway
            if tellmoveaway:
                if not self.placetimeout:
                    # Request other units to move away (might fail)
                    for unit in tellmoveaway:
                        if not unit or unit == outer:
                            continue
                        distance = (unit.GetAbsOrigin() - order.position).Length2D()
                        try:
                            unit.DispatchEvent('OnRequestMoveAway', order.position,
                                self.maxrange - distance + unit.CollisionProp().BoundingRadius2D() + 16.0)
                        except AttributeError:
                            PrintWarning('ActionPlaceObject.Update: %s is not a unit' % (str(unit)))
                            continue

                    # Tell the builder to move away from the spot
                    if outer in tellmoveaway:
                        distance = (unit.GetAbsOrigin() - order.position).Length2D()
                        if not self.movedaway and distance < self.maxrange * 0.85:
                            distance = self.maxrange - distance + outer.CollisionProp().BoundingRadius2D() + 16.0
                            dir = (order.position - outer.GetAbsOrigin())
                            dir.z = 0.0
                            self.movedaway = True
                            return self.SuspendFor(self.behavior.ActionMoveAway, 'Moving away from construction spot', -dir, (distance/outer.mv.maxspeed))

                    self.placetimeout = gpGlobals.curtime + 8.0

                # NOTE: Allow placing the building through the builder.
                if len(tellmoveaway) > 1 or tellmoveaway[0] != outer:
                    return self.Continue()

            # Complete ability before clearing the order (otherwise it results in canceling the ability)
            # Clear order before placing, because PostPlaceObject might insert a new order.
            order.ability.SetRecharge(units=outer)
            order.ability.Completed()
            order.Remove(dispatchevent=False)

            object = order.ability.DoPlaceObject()
            self.PostPlaceObject(object)

            # PostPlaceObject might have caused a transition already.
            if not self.valid:
                return
            return self.ChangeTo(self.behavior.ActionIdle, 'Placed object')

        def PostPlaceObject(self, object):
            pass

        placetimeout = None

        movedaway = False

    class ActionPlaceBuilding(ActionPlaceObject):
        def PostPlaceObject(self, object):
            if not object.autoconstruct:
                leftpressed = MouseTraceData()
                leftpressed.ent = object

                constructability = object.constructability
                if constructability in self.outer.abilitiesbyname:
                    abi = self.outer.DoAbility(constructability, [('leftpressed', leftpressed)], autocasted=True)
                    if abi:
                        abi.autocasted = False

    # Climbing actions
    class ActionStartClimbing(BaseAction):
        """ Generic action to start climbing up something.
            Ensures the unit is facing the right direction.

            Calls StartClimbing when ready and then by default changes to ActionClimb.
        """
        def Init(self, climbheight, direction):
            """ Action start climbing init.

                Args:
                   climbheight (float): Height the unit should climb.
                   direction (Vector): Direction of the target position (Vector)
            """
            self.climbheight = climbheight
            self.direction = direction

        def OnStart(self):
            angles = QAngle()
            VectorAngles(self.direction, angles)
            if AngleDiff(angles.y, self.outer.GetAbsAngles().y) > self.facingtolerance:
                return self.SuspendFor(self.behavior.ActionFaceYaw, 'Not facing climb direction', angles.y)
            return self.StartClimbing()

        def OnResume(self):
            # Should be facing now, might want to recheck?
            return self.StartClimbing()

        def StartClimbing(self):
            if self.outer.climbdismountz > self.climbheight:
                self.outer.DoAnimation(self.outer.ANIM_CLIMBDISMOUNT)
                return self.ChangeTo(self.behavior.ActionClimbDismount, 'Climbing..', self.outer.GetAbsOrigin().z + self.climbheight,
                                     activity=self.outer.animstate.specificmainactivity, transitionaction=self.behavior.ActionIdle)
            return self.ChangeTo(self.behavior.ActionClimb, 'Climbing..', self.climbheight)

        facingtolerance = 5.0

    class ActionClimb(BaseAction):
        """ This action loops the climb action until the unit
            climbed up the specified height. It uses the predefined animation
            movement to make it climb up. In case the target height is reached,
            the unit z value is clamped.
        """
        def Init(self, climbheight):
            """ Inialize method.

                Args:
                   climbheight (float): Height the unit should climb.
            """
            self.climbheight = climbheight

        def OnStart(self):
            self.startz = self.outer.GetAbsOrigin().z
            self.desiredz = self.startz + self.climbheight
            minmaxs = Vector(8, 8, 1)
            #ndebugoverlay.Box(self.outer.GetAbsOrigin(), -minmaxs, minmaxs, 255, 0, 0, 100, 10.0)
            #ndebugoverlay.Box(self.outer.GetAbsOrigin() + Vector(0, 0, self.desiredz - self.startz), -minmaxs, minmaxs, 0, 255, 0, 100, 10.0)
            self.outer.AddFlag(FL_FLY)
            self.outer.locomotionenabled = False
            self.outer.climbing = True
            self.outer.UpdateServerAnimation() # Extra update to ensure the correct animation is running for automovement
            if self.CheckArrived():
                self.outer.DoAnimation(self.outer.ANIM_CLIMBDISMOUNT)
                return self.ChangeTo(self.behavior.ActionClimbDismount, 'Done climbing, dismounting..', self.desiredz,
                                     activity=self.outer.animstate.specificmainactivity, transitionaction=self.behavior.ActionIdle)

        def OnEnd(self):
            self.outer.RemoveFlag(FL_FLY)
            self.outer.locomotionenabled = True
            self.outer.climbing = False
            #UTIL_DropToFloor(self.outer, MASK_NPCSOLID)

        def CheckArrived(self):
            curz = self.outer.GetAbsOrigin().z
            if (curz - self.startz) >= self.climbheight - self.outer.climbdismountz - 1.0: # Assume the dismount will travel another x units
                return True
            return False

        def Update(self):
            self.outer.AutoMovement()
            cur = self.outer.GetAbsOrigin()
            if self.CheckArrived():
                self.outer.DoAnimation(self.outer.ANIM_CLIMBDISMOUNT)
                return self.ChangeTo(self.behavior.ActionClimbDismount, 'Done climbing, dismounting..', self.desiredz,
                                     activity=self.outer.animstate.specificmainactivity, transitionaction=self.behavior.ActionIdle)
            return self.Continue()

    class ActionClimbDismount(BaseBehavior.ActionWaitForActivityTransitionAutoMovement):
        """ Called when the desired height is reached.
            Plays the dismount animation.
        """
        def Init(self, desiredz, *args, **kwargs):
            """ Inialize method.

                Args:
                   desiredz (float): The desired target z. The unit z is clamped to this value and the tolerance.
            """
            self.desiredz = desiredz
            super().Init(*args, **kwargs)

        def OnStart(self):
            self.outer.AddFlag(FL_FLY)
            self.outer.locomotionenabled = False
            return super().OnStart()

        def Update(self):
            transition = super().Update()
            cur = self.outer.GetAbsOrigin()
            if cur.z > self.desiredz + self.outer.dismounttolerancez:
                cur.z = self.desiredz + self.outer.dismounttolerancez
                self.outer.SetLocalOrigin(cur)
            #    UTIL_DropToFloor(self.outer, MASK_NPCSOLID)
            return transition

        def OnEnd(self):
            self.outer.RemoveFlag(FL_FLY)
            self.outer.locomotionenabled = True
            UTIL_DropToFloor(self.outer, MASK_NPCSOLID)
            return super().OnEnd()

    # Charging (hunter, antlion guard)
    class ActionPreChargeMove(BaseBehavior.ActionAbility):
        """ Move in range and face target """
        def Update(self):
            ability = self.order.ability
            target = self.order.target if self.order.target else self.order.position
            targetpos = self.order.target.GetAbsOrigin() if self.order.target else self.order.position

            # In range?
            minfacingcone = ability.minfacingcone
            startchargedist = ability.startchargedist
            #dist = (targetpos - self.outer.GetAbsOrigin()).Length2D()
            if not self.inrangeandfacing:
                return self.SuspendFor(self.behavior.ActionMoveInRangeAndFace, 'Not in range of target', target, maxrange=startchargedist, facingcone=minfacingcone)

            return self.ChangeTo(self.behavior.ActionChargeMove, "In range and facing target", self.order)

        def OnResume(self):
            self.inrangeandfacing = True
            return super().OnResume()

        inrangeandfacing = False

    class ActionChargeMove(BaseBehavior.ActionAbility):
        def OnStart(self):
            # Take movement control
            outer = self.outer
            ability = self.order.ability
            self.oldyawspeed = outer.mv.yawspeed
            self.oldmaxspeed = outer.mv.maxspeed
            outer.chargehitunits = set() # Reset hit units
            outer.mv.yawspeed = ability.yawturnspeed # Make turning very slow
            outer.navigator.StopMoving() # Make sure we are not already moving
            outer.aimoving = True
            outer.DoAnimation(outer.ANIM_STARTCHARGE)
            self.startposition = outer.GetAbsOrigin()
            self.maxchargedist = ability.maxchargedist

        def OnEnd(self):
            # Give back movement control to locomotion component
            self.outer.aimoving = False
            self.outer.mv.maxspeed = self.oldmaxspeed
            self.outer.mv.yawspeed = self.oldyawspeed

        def Update(self):
            outer = self.outer
            order = self.order

            outer.ChargeLookAhead()

            origin = outer.GetAbsOrigin()
            dist = (self.startposition - origin).Length2D()

            # GetIdealSpeed corresponds to the current sequence speed
            speedmod = order.ability.speedmod
            speedoverride = order.ability.speedoverride
            outer.mv.maxspeed = speedoverride * speedmod if speedoverride else outer.GetIdealSpeed() * speedmod
            outer.mv.forwardmove = outer.mv.maxspeed

            impacttype = -1

            if outer.mv.blockers:
                for blocker in outer.mv.blockers:
                    if not blocker:
                        continue
                    impacttype = outer.HandleChargeImpact(origin, blocker)
                    break
            elif dist > self.maxchargedist:
                impacttype = 2

            if impacttype == 1:
                self.chargeending = True
                order.Remove(dispatchevent=False)
                outer.DoAnimation(outer.ANIM_CRASHCHARGE)
                return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Impact',
                                     outer.animstate.specificmainactivity, self.behavior.ActionIdle)
            elif impacttype == 2:
                self.chargeending = True
                order.Remove(dispatchevent=False)
                outer.DoAnimation(outer.ANIM_STOPCHARGE)
                return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Impact entity',
                                     outer.animstate.specificmainactivity, self.behavior.ActionIdle)
            return self.Continue()

        def OnNewOrder(self, order):
            self.outer.DoAnimation(self.outer.ANIM_STOPCHARGE)
            return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Order received, stopping charge',
                                 self.outer.animstate.specificmainactivity, self.behavior.ActionIdle)

        def OnAllOrdersCleared(self):
            self.outer.DoAnimation(self.outer.ANIM_STOPCHARGE)
            return self.ChangeTo(self.behavior.ActionWaitForActivityTransition, 'Order cleared, stopping charge',
                                 self.outer.animstate.specificmainactivity, self.behavior.ActionIdle)

        chargeending = False

    class ActionChanneling(BaseBehavior.ActionWait):
        """ Causes the unit to stop acting until the channeling action is completed. """
        channelsuccess = False
        channel_animation = None
        channeltime = 0
        ability = None

        def Init(self, channeltime, ability=None, channel_animation=None):
            super().Init(channeltime)

            self.channeltime = channeltime
            self.ability = ability
            self.channel_animation = channel_animation

        def OnStart(self):
            outer = self.outer

            if self.channeltime > 0:
                outer.channeltime = (gpGlobals.curtime, gpGlobals.curtime + self.channeltime)
            if self.channel_animation:
                outer.DoAnimation(self.channel_animation)

            return super().OnStart()

        def OnEnd(self):
            super().OnEnd()

            outer = self.outer
            outer.channeltime = None

        def OnWaitFinished(self):
            self.channelsuccess = True