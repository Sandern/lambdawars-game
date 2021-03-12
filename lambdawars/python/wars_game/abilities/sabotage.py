from vmath import vec3_angle
from core.abilities import AbilityTarget
from core.units import GetUnitInfo
from entities import D_HT

if isserver:
    from core.units import BaseBehavior
    
def IsValidSabotageTarget(unit, target):
    if not target or not target.IsUnit():
        return False
        
    if not unit.IRelationType(target) == D_HT:
        return False
        
    unitinfo = target.unitinfo
     
    validunittypes = [
        'floor_turret',
        'combine_mine',
        'build_reb_barracks',
        'build_reb_barracks_destroyhq',
        'build_reb_munitiondepot',
        'build_reb_munitiondepot_destroyhq',
        'build_reb_specialops',
        'build_reb_specialops_destroyhq',
        'build_reb_billet',
        'build_reb_billet_destroyhq',
        'build_reb_vortigauntden',
        'build_reb_vortigauntden_destroyhq',
        'build_comb_mech_factory',
        'build_comb_garrison',
        'build_comb_headcrabcanisterlauncher',
        'build_comb_mortar',
        'comb_mountableturret',
        'build_comb_regenerationpost',
        'build_reb_barreltrap',
        'build_reb_barreltrap_destroyhq',
        'build_reb_detectiontower',
        'build_reb_detectiontower_destroyhq',
        'build_reb_radiotower',
        'build_reb_radiotower_destroyhq',
        'build_reb_teleporter',
        'build_reb_teleporter_destroyhq',
        'rebels_mountableturret',
        'build_reb_barricade',
        'build_comb_armory',
        'build_comb_specialops',
        'build_comb_synthfactory',
        'build_comb_barricade',
        'build_comb_energycell',
        'build_comb_powergenerator',
        'build_comb_powergenerator_scrap',
        'build_reb_junkyard',
        'build_reb_junkyard_destroyhq',
        'build_reb_triagecenter',
        'build_reb_triagecenter_destroyhq',
        'build_reb_techcenter',
        'build_comb_tech_center',
    ]
    isvalidunittype = False
    for unittype in validunittypes:
        validunitinfo = GetUnitInfo(unittype, fallback=None)
        if not validunitinfo:
            continue
        if issubclass(unitinfo, validunitinfo):
            isvalidunittype = True
            break
        
    if not isvalidunittype:
        return False

    return True
        
if isserver:
    class ActionSabotage(BaseBehavior.ActionAbility):
        def Update(self):
            outer = self.outer

            abi = self.order.ability
            target = self.order.target
            if not target:
                abi.Cancel()
                self.order.Remove(dispatchevent=False)
                return self.Continue()
            
            # In range of target
            if not self.movedtospot:
                self.movingtospot = True
                return self.SuspendFor(self.behavior.ActionMoveTo, 'Moving to target', target) 
                
            # Facing?
            if not outer.FInAimCone(target, self.facingminimum):
                return self.SuspendFor(self.behavior.ActionFaceTarget, 'Not facing target', target, self.facingminimum)

            if not abi.TakeEnergy(self.outer):
                abi.Cancel(cancelmsg='#Ability_NotEnoughEnergy')
                self.order.Remove(dispatchevent=False)
                return self.Continue()

            trans = self.SuspendFor(self.behavior.ActionChanneling, 'Sabotaging', 11.2)
            self.sabotagingaction = self.nextaction
            return trans
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.sabotaged:
                self.order.ability.Cancel()

        def OnResume(self):
            outer = self.outer
            target = self.order.target
            abi = self.order.ability
            if self.movingtospot:
                self.movingtospot = False
                self.movedtospot = self.outer.navigator.path.success
            elif self.sabotagingaction:
                if self.sabotagingaction.channelsuccess and IsValidSabotageTarget(outer, target):
                    # Change the target to the new owner and new rotation. Mark as reprogrammed.
                    target.reprogrammed = True
                    target.SetOwnerNumber(outer.GetOwnerNumber())
                    if abi.targetangle != vec3_angle:
                        target.SetAbsAngles(abi.targetangle)
                        
                    abi.SetRecharge(outer)
                    abi.Completed()
                    self.order.Remove(dispatchevent=False)
                    self.sabotaged = True
                self.sabotagingaction = None
                
            return super().OnResume()
            
        sabotaged = False
        movingtospot = False
        movedtospot = False
        sabotagingaction = None
        facingminimum = 0.7


# Spawns a grenade
class AbilitySabotage(AbilityTarget):
    # Info
    name = "sabotage"
    image_name = 'vgui/rebels/abilities/rebel_saboteur_sabotage.vmt'
    rechargetime = 1
    costs = []
    energy = 25
    displayname = "#AbilitySabotage_Name"
    description = "#AbilitySabotage_Description"
    cloakallowed = True
    allowmultipleability = True
    activatesoundscript = 'ability_sabotage'
    requirerotation = False
    sabotagetarget = None

    def DetermineRequireRotation(self):
        mousedata = self.player.GetMouseData()
        if not mousedata:
            return

        target = mousedata.ent

        if not IsValidSabotageTarget(self.unit, target):
            return

        self.requirerotation = target.unitinfo.name == 'floor_turret'

    if isserver:
        def OnLeftMouseButtonPressed(self):
            self.DetermineRequireRotation()

            ret = super().OnLeftMouseButtonPressed()
            
            if self.mousedata:
                data = self.mousedata
                target = data.ent

                if not self.unit:
                    self.Cancel(cancelmsg='Lost unit', debugmsg='No longer a unit available for this ability')
                    return
                
                if not IsValidSabotageTarget(self.unit, target):
                    self.Cancel(cancelmsg='Invalid target', debugmsg='Not disliking the target')
                    return True
                
            return ret
                
        def DoAbility(self):
            data = self.mousedata
            
            if self.ischeat:
                self.Completed()
                return

            pos = data.groundendpos
            target = data.ent
            
            if not self.unit:
                self.Cancel(cancelmsg='Lost unit', debugmsg='No longer a unit available for this ability')
                return
            
            if not IsValidSabotageTarget(self.unit, target):
                self.Cancel(cancelmsg='Invalid target', debugmsg='Not disliking the target')
                return

            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            self.sabotagetarget = target
            self.unit.AbilityOrder(position=pos,
                        target=target,
                        ability=self)
            self.SetNotInterruptible()
            
        behaviorgeneric_action = ActionSabotage
    else:
        sabotageoriginalangles = None
        visualscleared = False

        def OnLeftMouseButtonPressed(self):
            self.DetermineRequireRotation()
            return super().OnLeftMouseButtonPressed()
        
        def Frame(self):
            super().Frame()
            
            if self.stopupdating or self.visualscleared:
                return
                
            if not self.mousedata:
                return
                
            data = self.mousedata
            target = data.ent
            
            if not IsValidSabotageTarget(self.unit, target):
                return

            if not self.sabotagetarget:
                self.sabotagetarget = target
                self.sabotageoriginalangles = target.GetAbsAngles()
            
            self.sabotagetarget.SetRenderColor(0, 255, 0)
            if self.targetangle != vec3_angle:
                self.sabotagetarget.SetAbsAngles(self.targetangle)
            
        def ClearVisuals(self):
            super().ClearVisuals()
            
            self.visualscleared = True
            if self.sabotagetarget:
                self.sabotagetarget.SetAbsAngles(self.sabotageoriginalangles)
                self.sabotagetarget.SetRenderColor(255, 255, 255)
