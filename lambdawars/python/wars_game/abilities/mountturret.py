from srcbase import IN_SPEED
from core.abilities import AbilityTarget
from playermgr import ListAlliesOfOwnerNumber

def CanMountTurret(unit, target):
    if not target or target.IsWorld() or not target.IsUnit():
        return False, '#Ability_InvalidTarget'
    
    # TODO: Need better check for testing if it is a turret
    if not target.ismountableturret:
        return False, '#MountTur_NotATurret'
        
    owner = target.GetOwnerNumber()        
    unitowner = unit.GetOwnerNumber()
    owners = ListAlliesOfOwnerNumber(owner)
    unitowners = ListAlliesOfOwnerNumber(unitowner)
    # Can't mount turret of someone else
    for owner in owners:
        if unitowners != owners:
            return False, '#MountTur_NotMine'
        
    # Should be constructed
    if not target.constructionstate is target.BS_CONSTRUCTED:
        return False, '#MountTur_NotConstructed'

    # Check if not yet occupied
    if target.controller:
        return False, '#MountTur_AlreadyMounted'
        
    return True, None
def CanMountEnemyTurret(unit, target):
    owner = target.GetOwnerNumber()        
    unitowner = unit.GetOwnerNumber()
    owners = ListAlliesOfOwnerNumber(owner)
    unitowners = ListAlliesOfOwnerNumber(unitowner)
    # Can't mount turret of someone else
        
    for owner in owners:
        if unitowners != owners:
            return False, '#MountTur_NotMine'
    return True, None

if isserver:
    from core.units.intention import BaseAction
    from core.units import BehaviorGeneric
    from unit_helper import GF_OWNERISTARGET, GF_USETARGETDIST
    
    TOLERANCE = 8.0
    
    class ActionMoveToTurret(BehaviorGeneric.ActionMoveTo):
        def Init(self, turret=None, *args, **kwargs):
            super().Init(turret.manpoint, *args, tolerance=TOLERANCE-1, **kwargs)
            self.turret = turret
        
        def Update(self):
            canmount, reason = CanMountTurret(self.outer, self.turret)
            if not canmount:
                return self.Done("Turret no longer mountable")
        
            return super().Update()

    class ActionMountTurret(BehaviorGeneric.ActionAbility):
        def CheckNearTurret(self):
            # Check turret alive
            if not self.turret or not self.turret.IsAlive():
                self.order.Remove(dispatchevent=False)
                return self.ChangeTo(self.behavior.ActionIdle, "Turret went None. Died?")
                
            canmount, reason = CanMountTurret(self.outer, self.turret)
            if not canmount:
                self.order.Remove(dispatchevent=False)
                return self.ChangeTo(self.behavior.ActionIdle, "Turret no longer mountable")
                
            #if not self.movedtoturret:
            #    self.movedtoturret = True
            #    return self.SuspendFor(self.behavior.ActionMoveTo, "Moving to turret", self.turret, 32.0, goalflags=GF_OWNERISTARGET|GF_USETARGETDIST)
                
            # Check if we are on the manpoint
            dist = (self.turret.manpoint - self.outer.GetLocalOrigin()).Length2D()
            if dist > TOLERANCE:
                return self.SuspendFor(ActionMoveToTurret, "Moving to manpoint (dist: %d)" % (dist), turret=self.turret, goalflags=GF_OWNERISTARGET|GF_USETARGETDIST)
            
            # Enter the mount action
            return self.SuspendFor(ActionControlTurret, "On manpoint, start control turret", self.turret)
            
        def OnStart(self):
            self.turret = self.order.target
            return self.CheckNearTurret()
            
        def OnResume(self):
            return self.CheckNearTurret()
            
        def OnStunned(self):
            return self.ChangeTo(self.behavior.ActionStunned, 'Changing to stunned action')
        
        #movedtoturret = False
            
    class ActionControlTurret(BaseAction):
        def Init(self, turret):
            self.turret = turret.GetHandle()
        
        def OnStart(self):
            # Take movement control
            self.outer.navigator.StopMoving()
            self.outer.aimoving = True
            self.outer.Mount()
            self.firetime = 0.0
            if self.turret:
                self.turret.OnStartControl(self.outer)
                self.turret.yawturnspeed = self.outer.mv.yawspeed
        
        def OnEnd(self):
            # Give back movement control and clear facing
            self.outer.Dismount()
            self.outer.aimoving = False
            self.outer.navigator.idealyaw = -1
            if self.turret:
                self.turret.enemy = None
                self.turret.OnLeftControl()
        
        def Update(self):
            outer = self.outer
            turret = self.turret
            
            # Check turret alive
            if not turret or not turret.IsAlive():
                return self.Done("Turret went None. Died?")
            canmount, reason = CanMountEnemyTurret(self.outer, self.turret)
            if not canmount:
                self.Done("Turret no longer mountable")

            # Update facing yaw
            if outer.navigator.idealyaw != turret.aimyaw:
                outer.navigator.idealyaw = turret.aimyaw
            
            # Update turret enemy (turret will always point to the target)
            # Use the sensing component of the turret, since it is setup to detect within the range of the turret
            # TODO: Maybe clamp turret sensing to our own sensing? However might not be needed since the fog of war already takes care of that.
            turret.senses.PerformSensing()
            turret.UpdateEnemy(turret.senses)
            enemy = turret.enemy
            
            # Fire if in our aim cone
            if enemy:
                attackinfo = turret.unitinfo.AttackTurret
                dist = (enemy.GetAbsOrigin() - turret.GetAbsOrigin()).Length2D()
                if dist < attackinfo.maxrange and turret.InTurretAimCone(enemy, attackinfo.cone):    
                    self.firetime += outer.think_freq
                    bulletcount = 0

                    while self.firetime > attackinfo.attackspeed:
                        bulletcount += 1
                        self.firetime -= attackinfo.attackspeed
                    if bulletcount:
                        self.turret.Fire(bulletcount, outer)
            
            return self.Continue()
            
class AbilityMountTurret(AbilityTarget):
    # Info
    name = 'mountturret'
    displayname = '#MountTur_Name'
    description = '#MountTur_Description'
    image_name = 'vgui/abilities/mountturret'
    hidden = True
    cloakallowed = True
    
    @classmethod
    def OverrideOrder(cls, unit, data, player):
        canmount, reason = CanMountTurret(unit, data.ent)
        if canmount:
            if isserver:
                unit.DoAbility('mountturret', [('leftpressed', data)], queueorder=player.buttons & IN_SPEED)
            return True
        return False
        
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata

            target = data.ent if (data.ent and not data.ent.IsWorld()) else None
            
            canmount, reason = CanMountTurret(self.unit, target)
            if not canmount:
                self.Cancel(cancelmsg=reason)
                return

            self.unit.AbilityOrder(ability=self, target=target, position=data.endpos)
            self.Completed()
                
        behaviorgeneric_action = ActionMountTurret