from srcbase import MASK_NPCSOLID, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS
from core.abilities import AbilityTargetGroup, AbilityTarget
from entities import MouseTraceData
from utils import trace_t, UTIL_TraceLine
            
class AbilityCharge(AbilityTargetGroup):
    # Info
    name = "charge"
    image_name = 'vgui/abilities/charge.vmt'
    rechargetime = 7
    displayname = "#AbilityCharge_Name"
    description = "#AbilityCharge_Description"
    hidden = True
    maxchargedist = 1500
    startchargedist = maxchargedist * 0.85
    minfacingcone = 0.88
    speedmod = 1.2 # Modifies the charge speed, which is based on the animation
    speedoverride = 0 # Overrides animation defined speed
    yawturnspeed = 4 # Degrees per second
    
    defaultautocast = True
    autocastcheckonenemy = True
    
    # Ability
    if isserver:
        def DoAbility(self):
            data = self.mousedata
            
            target = data.ent
            if target and target.IsWorld():
                target = None

            for unit in self.units:
                self.behaviorgeneric_action = unit.behaviorgeneric.ActionPreChargeMove
                self.AbilityOrderUnits(unit, 
                    position=data.endpos,
                    target=target,
                    ability=self
                )
            self.SetRecharge(self.units)
            self.Completed()
            
    @classmethod
    def CheckAutoCast(info, unit):
        # No autocasting if too close
        enemy = unit.enemy
        myorigin = unit.GetAbsOrigin()
        enemyorigin = enemy.GetAbsOrigin()
        #unitinfo = unit.unitinfo
        
        # Don't do this if too close or too far
        distsqr = enemyorigin.DistToSqr(myorigin)
        if distsqr < 256*256 or distsqr > info.startchargedist*info.startchargedist:
            return False
            
        # Only do this if we can do a straight trace
        tr = trace_t()
        UTIL_TraceLine(unit.EyePosition(), enemy.WorldSpaceCenter(), MASK_NPCSOLID, unit, WARS_COLLISION_GROUP_IGNORE_ALL_UNITS, tr)
        if tr.fraction != 1:
            #print(tr.fraction)
            return False
        
        if info.CanDoAbility(None, unit=unit):
            leftpressed = MouseTraceData()
            leftpressed.endpos = enemyorigin
            leftpressed.groundendpos = enemyorigin
            leftpressed.ent = enemy
            unit.DoAbility(info.name, mouse_inputs=[('leftpressed', leftpressed)])
            return True
        return False
            

class AbilityChargeHunter(AbilityCharge):
    # Info
    name = "chargehunter"
    image_name = 'vgui/combine/abilities/combine_hunter_charge.vmt'
    rechargetime = 10
    displayname = "#AbilityChargeHunter_Name"
    description = "#AbilityChargeHunter_Description"
    hidden = True
    minfacingcone = 0.99
    yawturnspeed = 7
    supportsautocast = True
    defaultautocast = False
    autocastcheckonenemy = True
    sai_hint = AbilityTarget.sai_hint | set(['sai_grenade'])
    
class AbilityChargeDog(AbilityCharge):
    # Info
    name = "dogcharge"
    image_name = 'vgui/combine/abilities/combine_hunter_charge.vmt'
    rechargetime = 5
    energy = 25
    displayname = "#AbilityChargeDog_Name"
    description = "#AbilityChargeDog_Description"
    hidden = True
    minfacingcone = 0.99
    yawturnspeed = 7
    speedoverride = 700
    supportsautocast = True
    defaultautocast = False
    autocastcheckonenemy = True
    