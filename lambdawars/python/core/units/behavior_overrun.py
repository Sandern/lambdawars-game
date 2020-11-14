from core.units import unitlist
from entities import gEntList, D_HT
import playermgr
import random

def CreateBehaviorOverrun(BaseClass):
    class BehaviorOverrun(BaseClass):
        """ Behavior made for overrun, but not restricted to that gamemode.
            Instead of taking orders, this behavior will pick a goal and do an attack
            move on that goal.
        """
        class ActionIdle(BaseClass.ActionIdle):
            """ The Overrun idle action searches for buildings and enemies to attacks and then
                issue's an attack move order.
            """
            # Always chase enemies directly, otherwise might wait in unreachable positions
            idlewaitmoveuntilunderattack = False 
            
            def Update(self):
                # Find enemies and do an attack move on them.
                enemy = (   self.FindRandomEnemyOfClasses(['build_comb_hq', 'build_reb_hq']) or
                            self.FindFirstEnemyFromUnitList() )
                if enemy:
                    outer = self.outer
                    if hasattr(outer, 'wavespawnpoint') and outer.wavespawnpoint:
                        wavespawnpoint = outer.wavespawnpoint
                        path = wavespawnpoint.GetPrecomputedPath(outer, enemy)
                        outer.wavespawnpoint = None # Don't use this path again
                        if path:
                            transition = self.SuspendFor(self.behavior.ActionAttackMove, 'Move attack enemy', enemy)
                            self.nextaction.savepath = path
                            return transition
                    return self.SuspendFor(self.behavior.ActionAttackMove, 'Move attack enemy', enemy)
                return self.Continue()
                
            def FindEnemyOfClass(self, classname):
                ent = gEntList.FindEntityByClassname(None, classname)
                while ent:
                    if ent.IsAlive() and playermgr.relationships[(self.outer.GetOwnerNumber(), ent.GetOwnerNumber())] == D_HT:
                        return ent
                    ent = gEntList.FindEntityByClassname(ent, classname)
                return None
                
            def FindRandomEnemyOfClasses(self, classnames):
                enemies = []
                for classname in classnames:
                    ent = gEntList.FindEntityByClassname(None, classname)
                    while ent:
                        if ent.IsAlive() and playermgr.relationships[(self.outer.GetOwnerNumber(), ent.GetOwnerNumber())] == D_HT:
                            enemies.append(ent)
                        ent = gEntList.FindEntityByClassname(ent, classname)
                if enemies:
                    return random.sample(enemies, 1)[0]
                return None
                
            def FindFirstEnemyFromUnitList(self):
                for ownernumber, l in unitlist.items():
                    if playermgr.relationships[(self.outer.GetOwnerNumber(), ownernumber)] != D_HT:
                        continue
                    for unit in l:
                        if unit.IsAlive():
                            return unit
                return None
                
        class ActionAttackMove(BaseClass.ActionAttackMove):
            """ Removes the Overrun enemy if the navigation of the attack move failed, but
                only if it didn't fail due the goal target dying and the unit should have no 
                active enemy.
                
                Doing this should detect if the unit got stuck and prevents progress of the waves.
                A removed unit is added back to the "to be spawned" count, since it was not killed.
            """
            def OnNavFailed(self):
                outer = self.outer
                targetdied = bool(not self.target or not self.target.IsAlive())
                if not targetdied and not outer.enemy:
                    PrintWarning("#%s: Removing Overrun enemy due failed navigation\n" % (outer.entindex()))
                    outer.SetThink(outer.SUB_Remove)
                    return self.Continue()
                return super().OnNavFailed()
            
    return BehaviorOverrun
