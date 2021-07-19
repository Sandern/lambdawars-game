from srcbase import SOLID_NONE, FSOLID_NOT_SOLID, COLLISION_GROUP_NONE, COLLISION_GROUP_DEBRIS, MOVETYPE_NONE
from vmath import Vector, QAngle
from core.abilities import AbilityAsAnimation, AbilityUpgrade
from fields import FloatField
from playermgr import OWNER_NEUTRAL
if isserver:
    from entities import CreateEntityByName, DispatchSpawn
    from utils import UTIL_PrecacheOther

class AbilityLarvalExtract(AbilityAsAnimation):
    # Info
    name = "larvalextract"
    rechargetime = 0.0
    energy = 0
    displayname = "#RebLarvalextract_Name"
    description = "#RebLarvalExtract_Description"
    image_name = 'vgui/rebels/abilities/larva_extract_ability'
    hidden = True
    costs = [('requisition', 15), ('scrap', 15)]
    #costs = [('requisition', 15)]
    techrequirements = ['larvalextract_unlock']
    set_initial_recharge = False
    maxantlions = 0

    sai_hint = AbilityAsAnimation.sai_hint | set(['sai_deploy']) # doesn't work as ability that can be used as grenade
    def DoAbility(self):
        self.SelectGroupUnits()
        for unit in list(self.units):
            unit.AbilityOrder(ability=self)

    def TryStartAnimation(self, unit):
        if not self.CanDoAbility(self.player, unit):
            return False
        if not self.TakeEnergy(unit):
            return False
        if not self.TakeResources(refundoncancel=True):
            return False
        self.DoAnimation(unit)
        return True

    @classmethod
    def GetRequirements(info, player, unit):
        requirements = super().GetRequirements(player, unit)
        if unit.larvalextract:
            requirements.add('alreadyupgraded')
        return requirements

    def DoAnimation(self, unit):
        if isserver:
            self.CreateBugbait(unit)
        unit.DoAnimation(unit.ANIM_VORTIGAUNT_LARVALEXTRACT)


    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()

            UTIL_PrecacheOther('bugbait')
        def CreateBugbait(self, unit):
            vecOrigin = Vector()
            angles = QAngle()
            attachment = unit.LookupAttachment("nectar")#unit.lefthandattachment
            unit.GetAttachment(attachment, vecOrigin, angles)
            
            bugbait = CreateEntityByName('bugbait')
            bugbait.SetOwnerNumber(unit.GetOwnerNumber())
            bugbait.SetAbsOrigin(vecOrigin)
            bugbait.SetAbsAngles(angles)
            bugbait.SetOwnerEntity(unit)
            bugbait.SetThrower(unit)
            bugbait.bugbaitability = self
            DispatchSpawn(bugbait)
            bugbait.SetSolid(SOLID_NONE)
            bugbait.SetMoveType(MOVETYPE_NONE)
            bugbait.SetCollisionGroup(COLLISION_GROUP_DEBRIS)
            bugbait.SetParent(unit, attachment)
            bugbait.SetModel('models/weapons/w_larval_essence.mdl')
            #bugbait.Detonate(target=unit)
            
            unit.bugbait = bugbait

    throwtarget = None
    summonantlions = False

    @classmethod
    def SetupOnUnit(info, unit):
        super().SetupOnUnit(unit)
        
        if getattr(unit, 'abibugbait_antlions', None) == None:
            unit.abibugbait_antlions = set()
            unit.abibugbait_lastspawntime = 0
            unit.abibugbait_spawnpenalty = 0
        
    @classmethod
    def OnUnitThink(info, unit):
        unit.abibugbait_antlions = set(filter(bool, unit.abibugbait_antlions))
class OverrunAbilityLarvalExtract(AbilityLarvalExtract):
    # Info
    name = "overrun_larvalextract"
    rechargetime = 0.0
    energy = 0
    costs = [('kills', 5)]
    techrequirements = []

class AbilityLarvalExtractUnlock(AbilityUpgrade):
    name = 'larvalextract_unlock'
    displayname = '#RebLarvalextractUnlock_Name'
    description = '#RebLarvalextractUnlock_Description'
    image_name = "VGUI/rebels/abilities/larva_extract_upgrade"
    #techrequirements = ['build_reb_hq', 'build_reb_barracks', 'build_reb_munitiondepot', 'build_reb_triagecenter', 'build_reb_specialops', 'build_reb_techcenter']
    buildtime = 50.0
    costs = [[('kills', 5)], [('requisition', 25), ('scrap', 25)]]
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])