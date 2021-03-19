from srcbase import DMG_BURN
from vmath import AngleVectors, Vector, VectorNormalize, DotProduct, vec3_origin
from .citizen import UnitInfo, UnitCitizen, GenerateModelList
from entities import entity, MOVETYPE_NONE
from core.abilities import AbilityUpgrade, AbilityUpgradeValue, SubMenu, AbilityTarget, GetTechNode
from core.units.abilities import AbilityTransformUnit
from core.units import UnitBaseCombatHuman as BaseClass, unitlistpertype
from fields import UpgradeField, BooleanField
from wars_game.buildings.baseregeneration import PassiveRegeneration
from particles import PrecacheParticleSystem, PATTACH_ABSORIGIN_FOLLOW

from wars_game.attributes import FireAttribute
if isserver:
    from entities import CreateEntityByName, DispatchSpawn, variant_t, eventqueue, CTakeDamageInfo, D_LI, CEntityFlame, SmokeTrail
    from utils import UTIL_EntitiesInSphere, UTIL_SetSize, UTIL_SetOrigin, UTIL_Remove
    from core.ents import CTriggerArea

if isserver:
    @entity('trigger_heal_area')
    class HealArea(CTriggerArea):
        def Precache(self):
            super().Precache()
            # PrecacheParticleSystem('pg_heal')

        def Spawn(self):
            self.Precache()

            super().Spawn()

            self.SetThink(self.HealThink, gpGlobals.curtime, 'HealThink')

        def Heal(self, unit, heal):
            """
            @type unit: core.units.base.UnitBase
            @type heal: float
            """
            # Must not be mechanic
            if 'mechanic' in unit.attributes:
                return

            if unit.health < unit.maxhealth:
                self.healing = True
                unit.health += min(heal, (unit.maxhealth - unit.health))
                # DispatchParticleEffect("pg_heal", PATTACH_ABSORIGIN_FOLLOW, entity)
                if hasattr(unit, 'EFFECT_DOHEAL'):
                    unit.DoAnimation(unit.EFFECT_DOHEAL)

        def HealThink(self):

            dt = gpGlobals.curtime - self.GetLastThink('HealThink')
            heal = int(round(dt * self.healrate))

            self.healing = False

            for entity in self.touchingents:
                if not entity:
                    continue
                # heal units inside bunkers
                if entity.IsUnit() and entity.isbuilding and entity.unitinfo.name in ['build_comb_bunker',
                                                                                      'overrun_build_comb_bunker',
                                                                                      'build_reb_bunker',
                                                                                      'overrun_build_reb_bunker']:
                    for unit in entity.units:
                        self.Heal(unit, heal)

                if not entity.IsUnit() or entity.isbuilding or entity.IRelationType(self) != D_LI:
                    continue

                self.Heal(entity, heal)

            self.SetNextThink(gpGlobals.curtime + 0.5, 'HealThink')

        #: Heal rate per second of this building
        healrate = 4
        #: Whether or not the area was healing units last think
        healing = False


@entity('unit_rebel', networked=True)
class UnitRebel(UnitCitizen):
    if isserver:
        def Precache(self):
            super().Precache()

            self.PrecacheScriptSound("unit_rebel_hurt")
            #  PrecacheParticleSystem('wars_levelup')

    def OnTakeDamage(self, dmginfo):
        if self.lasttakedamage and self.health > 0 and dmginfo.GetDamage() > 0:
            self.EmitSound('unit_rebel_hurt')
        return super().OnTakeDamage(dmginfo)
@entity('unit_rebel_csm', networked=True)
class UnitRebelCSM(UnitRebel):
    canshootmove = True

# Rebel engineer
@entity('unit_rebel_engineer', networked=True)
class UnitRebelEngineer(UnitRebel):
    constructactivity = 'ACT_BUILDING'
    constructweapon = 'weapon_hammer'
    constructmaxrange = 0
    
    # Activity list
    activitylist = list(UnitRebel.activitylist)
    activitylist.extend([
        'ACT_BUILDING',
    ])


@entity('mission_unit_rebel_engineer', networked=True)
class MissionUnitRebelEngineer(UnitRebelEngineer):
    constructactivity = 'ACT_BUILDING'
    constructweapon = 'weapon_hammer'
    constructmaxrange = 0
    
    # Activity list
    activitylist = list(UnitRebelEngineer.activitylist)
    activitylist.extend([
        'ACT_BUILDING',
    ])


#@entity('unit_rebel_flamer', networked=True)
#class UnitRebelFlamer(UnitRebel):
    #if isserver:
        #def Precache(self):
           # super().Precache()

          #  self.PrecacheScriptSound('unit_rebel_flamer_ignited')

    #def OnTakeDamage(self, dmginfo):
        #if not self.gastank_ignited:
            #angles = self.GetAbsAngles()
            #forward = Vector()
            #AngleVectors(angles, forward)

            #vec_damage_force = dmginfo.GetDamageForce()
            #VectorNormalize(vec_damage_force)
            #dot = DotProduct(forward, vec_damage_force)

            # Scale damage when shield is facing about 30 degrees
            #if dot > 0.97:
                #self.SetThink(self.ExplodeGasTankThink, gpGlobals.curtime + 2.5)
                #self.gastank_ignited = True
                #self.EmitSound('unit_rebel_flamer_ignited')
                #pFlame = CEntityFlame.Create(self, False)
                #if pFlame != None:
                    #pass # pFlame.SetLifetime(self.lifetime)

                #pSmokeTrail = SmokeTrail.CreateSmokeTrail()
                #if pSmokeTrail:
                    #pSmokeTrail.spawnrate = 80
                    #pSmokeTrail.particlelifetime = 0.8
                    #pSmokeTrail.startcolor = Vector(0.3, 0.3, 0.3)
                    #pSmokeTrail.endcolor = Vector(0.5, 0.5, 0.5)
                    #pSmokeTrail.startsize = 10
                    #pSmokeTrail.endsize = 40
                    #pSmokeTrail.spawnradius = 5
                    #pSmokeTrail.opacity = 0.4
                    #pSmokeTrail.minspeed = 15
                    #pSmokeTrail.maxspeed = 25
                    ##pSmokeTrail.SetLifetime(self.lifetime)
                    #pSmokeTrail.SetParent(self, 0)
                    #pSmokeTrail.SetLocalOrigin(vec3_origin)
                    #pSmokeTrail.SetMoveType(MOVETYPE_NONE)

        #return super().OnTakeDamage(dmginfo)

    #def ExplodeGasTankThink(self):
        #if self.gastank_exploded:
            #return
        #self.gastank_exploded = True

        #origin = self.GetAbsOrigin()

        #radius = 320.0

        #bomb = CreateEntityByName("env_explosion")
        #bomb.SetAbsOrigin(origin)
        #bomb.KeyValue("iMagnitude", "120")
        #bomb.KeyValue("DamageForce", "500")
        #bomb.KeyValue('iRadiusOverride', str(radius))
        #bomb.KeyValue("fireballsprite", "sprites/zerogxplode.spr")
        #bomb.KeyValue("rendermode", "5")
        #DispatchSpawn(bomb)
        #bomb.Activate()

        #value = variant_t()
        #eventqueue.AddEvent(bomb, "Explode", value, 0.1, None, None)
        #eventqueue.AddEvent(bomb, "kill", value, 1.0, None, None)

        # TODO: in a better way!?
        #attributes = {FireAttribute.name: FireAttribute(self)}
        #targets = UTIL_EntitiesInSphere(320, self.GetAbsOrigin(), radius, 0)
        #for target in targets:
            #if not target or not target.IsUnit():
                #continue

            #dmgInfo = CTakeDamageInfo(self, self, 0, DMG_BURN)
            #dmgInfo.SetDamagePosition(origin)
            #dmgInfo.attributes = attributes
            #dmgInfo.forcefriendlyfire = True

            #target.TakeDamage(dmgInfo)
        #return super().Suicide()

    # Does nothing at all? Works the same with or without it
    #def Event_Killed(self, info):
        #if self.gastank_ignited and not self.gastank_exploded:
            #self.ExplodeGasTankThink()

        #return super().Event_Killed(info)

    #gastank_ignited = BooleanField(value=False)
    #gastank_exploded = BooleanField(value=False)


@entity('unit_rebel_medic', networked=True)
class UnitRebelMedic(UnitRebel):
    energyregenrate = UpgradeField(value=1.0, abilityname='medic_regenerate_upgrade')
    maxenergy = UpgradeField(abilityname='medic_maxenergy_upgrade', cppimplemented=True)


class RebelShared(UnitInfo):
    cls_name = 'unit_rebel'
    health = 160
    population = 1
    attributes = ['light']
    modellist = GenerateModelList('REBEL')
    hulltype = 'HULL_HUMAN'
    abilities = {
        0: 'grenade',
        #1: 'rebel_grenade_upgrade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    sound_select = 'unit_rebel_select'
    sound_move = 'unit_rebel_move'
    sound_attack = 'unit_rebel_attack'
    sound_select_f = 'unit_rebel_f_select'
    sound_move_f = 'unit_rebel_f_move'
    sound_attack_f = 'unit_rebel_f_attack'
    sound_death = 'unit_rebel_death'
    sound_death_f = 'unit_rebel_f_death'
    sound_flamer_ignited = 'unit_rebel_flamer_ignited'
    sound_hurt = 'unit_rebel_hurt'
    cantakecover = True
    sai_hint = set(['sai_unit_combat'])

class RebelScoutInfo(RebelShared):
    name = 'unit_rebel_scout'
    displayname = '#RebScout_Name'
    description = '#RebScout_Description'
    cls_name = 'unit_rebel'
    health = 35
    maxspeed = 282.0
    buildtime = 14.0
    unitenergy = 50
    unitenergy_initial = 5
    population = 1
    #tier = 1
    costs = [('requisition', 10)]
    accuracy = 0.60
    image_name = 'vgui/rebels/units/unit_rebel_scout'
    modellist = GenerateModelList('SCOUT')
    abilities = {
        0: 'infiltrate_reb_scout',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['weapon_pistol']
    sai_hint = set(['sai_unit_scout'])
    viewdistance = 1024
    scrapdropchance = 0.0


class RebelSaboteurInfo(RebelShared):
    name = 'unit_rebel_saboteur'
    displayname = '#RebSaboteur_Name'
    description = '#RebSaboteur_Description'
    #cls_name = 'unit_rebel_saboteur'
    health = 60
    maxspeed = 232.0
    viewdistance = 896
    buildtime = 22.0
    unitenergy = 100
    unitenergy_initial = 40
    population = 1
    costs = [('requisition', 15), ('scrap', 10)]
    #techrequirements = ['build_reb_munitiondepot']
    image_name = 'vgui/rebels/units/unit_rebel_saboteur'
    attributes = ['medium']
    #tier = 3 
    abilities = {
        0: 'infiltrate',
        1: 'c4explosive',
        2: 'sabotage',
        3: 'destroyhq_rebel_mine',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['weapon_pistol']
    sai_hint = set([])


@entity('unit_rebel_partisan', networked=True)
class UnitRebelPartisan(UnitRebel):
    maxhealth = UpgradeField(abilityname='armyrebels_tier_1', cppimplemented=True)
    health = UpgradeField(abilityname='armyrebels_tier_1', cppimplemented=True)


@entity('unit_rebel_partisan_molotov', networked=True)
class UnitRebelPartisanMolotov(UnitRebel):
    maxhealth = UpgradeField(abilityname='armyrebels_tier_1', cppimplemented=True)
    health = UpgradeField(abilityname='armyrebels_tier_1', cppimplemented=True)


class RebelPartisanInfo(RebelShared):
    name = 'unit_rebel_partisan'
    cls_name = 'unit_rebel_partisan'
    displayname = '#RebPartisan_Name'
    description = '#RebPartisan_Description'
    buildtime = 14.0
    health = 75
    population = 1
    maxspeed = 224.0
    viewdistance = 768
    scrapdropchance = 0.0
    #tier = 1
    modellist = GenerateModelList('DEFAULT')
    costs = [[('requisition', 10)], [('kills', 1)]]
    image_name = 'vgui/rebels/units/unit_rebel_partisan'
    attributes = ['light']
    abilities = {
        0: 'revolutionaryfervor',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['weapon_smg1']
    accuracy = 0.75
    #accuracy = 'low'


class DestroyHQRebelPartisanInfo(RebelPartisanInfo):
    name = 'unit_rebel_partisan_destroyhq'

''''@entity('unit_rebel_partisan_molotov', networked=True)
class UnitRebelPartisanMolotov(UnitCitizen):
    health = UpgradeField(abilityname='army_tier1', cppimplemented=True)'''


class RebelPartisanMolotovInfo(RebelPartisanInfo):
    name = 'unit_rebel_partisan_molotov'
    cls_name = 'unit_rebel_partisan_molotov'
    displayname = '#RebPartisanMolotov_Name'
    description = '#RebPartisanMolotov_Description'
    costs = [[('requisition', 10)], [('kills', 1)]]
    image_name = 'vgui/rebels/units/unit_rebel_partisan_molotov'
    buildtime = 10.0
    health = 75
    selectionpriority = 1
    weapons = []
    abilities = {
        0: 'throwmolotov',
        1: 'throwstinkbomb',
        2: 'revolutionaryfervor',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    sai_hint = set(['sai_unit_combat'])


class ArmyTier1Upgrade(AbilityUpgradeValue):
    name = 'armyrebels_tier_1'
    displayname = '#ArmyRebels_Tier_1_Name'
    description = '#ArmyRebels_Tier_1_Description'
    #techrequirements = ['mechanics_tier3']
    upgradevalue = 160


class DestroyHQRebelPartisanMolotovInfo(RebelPartisanMolotovInfo):
    name = 'unit_rebel_partisan_molotov_destroyhq'


@entity('unit_rebel_grenade_upgrade', networked=True)
class UnitRebelGrenadeUpgradeShared(UnitCitizen):
    def GetRequirements(self, requirements, info, player):
        super().GetRequirements(requirements, info, player)

        #if info.name == 'grenade':
        #    if not self.grenadeUnlocked:
        #        requirements.add('needsupgrade')

    def OnGrenadeUnlockedChanged(self):
        self.UpdateTranslateActivityMap()
        self.UpdateAbilities()

    if isserver:
        def Precache(self):
            super().Precache()

            self.PrecacheScriptSound("unit_rebel_hurt")

    def OnTakeDamage(self, dmginfo):
        if self.lasttakedamage and self.health > 0 and dmginfo.GetDamage() > 0:

            self.EmitSound('unit_rebel_hurt')
        return super().OnTakeDamage(dmginfo)
        
    grenadeUnlocked = BooleanField(value=False, networked=True, clientchangecallback='OnGrenadeUnlockedChanged')


class RebelInfo(RebelShared):
    name = 'unit_rebel'
    cls_name = 'unit_rebel_grenade_upgrade' # adds grenade unlock per unit this also needs the rebel_grenade_upgrade ability
    buildtime = 21.0
    costs = [[('requisition', 20)], [('kills', 1)]]
    maxspeed = 224.0
    viewdistance = 768
    displayname = '#RebSMG_Name'
    description = '#RebSMG_Description'
    image_name = 'vgui/rebels/units/unit_rebel'
    weapons = ['weapon_smg1']
    attributes = ['medium']
    techrequirements = ['build_reb_munitiondepot']
    #tier = 2
    abilities = {
        0: 'grenade',
        #1: 'rebel_grenade_upgrade',
        5: 'rebel_transform_sg',
        6: 'rebel_transform_ar2',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class DestroyHQRebelInfo(RebelInfo):
    name = 'unit_rebel_destroyhq'
    techrequirements = ['build_reb_munitiondepot_destroyhq']


class TutorialRebelInfo(RebelInfo):
    name = 'tutorial_rebel'
    techrequirements = []  


class RebelSGInfo(RebelInfo):
    name = 'unit_rebel_sg'
    displayname = '#RebSG_Name'
    description = '#RebSG_Description'
    buildtime = 23.0
    health = 160
    costs = [[('requisition', 20), ('scrap', 5)], [('kills', 1)]]
    techrequirements = ['build_reb_munitiondepot','weaponsg_unlock']
    #techrequirements = ['build_reb_munitiondepot']
    weapons = ['weapon_shotgun']
    abilities = {
        0: 'grenade',
        #1: 'rebel_grenade_upgrade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }

    attributes = ['medium']
    image_name = 'vgui/rebels/units/unit_rebel_sg'
    maxspeed = 248.0
    viewdistance = 768


class DestroyHQRebelSGInfo(RebelSGInfo):
    name = 'unit_rebel_sg_destroyhq'
    techrequirements = ['build_reb_munitiondepot_destroyhq','weaponsg_unlock']


class RebelAR2Info(RebelInfo):
    name = 'unit_rebel_ar2'
    displayname = '#RebAR2_Name'
    description = '#RebAR2_Description'
    buildtime = 25.0
    maxspeed = 208
    viewdistance = 832
    costs = [[('requisition', 20), ('scrap', 10)], [('kills', 2)]]
    techrequirements = ['build_reb_munitiondepot','weaponar2_unlock']
    accuracy = 0.626
    #techrequirements = ['build_reb_munitiondepot']
    weapons = ['weapon_ar2']
    abilities = {
        0: 'grenade',
        #1: 'rebel_grenade_upgrade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    sensedistance = 1024.0
    attributes = ['medium']
    image_name = 'vgui/rebels/units/unit_rebel_ar2'
	
class RebelTauInfo(RebelInfo):
    name = 'unit_rebel_tau'
    displayname = '#RebTau_Name'
    description = '#RebTau_Description'
    buildtime = 35.0
    maxspeed = 200
    health = 200
    viewdistance = 896
    scale = 1.0
    costs = [[('requisition', 60), ('scrap', 30)], [('kills', 2)]]
    #accuracy = 5.0
    population = 2
    modelname = 'models/rebel_tau.mdl'
    #techrequirements = ['build_reb_techcenter']
    selectionpriority = 4
    weapons = ['weapon_tau']
    abilities = {
		0: 'tau_alt_fire',
		7: 'mountturret',
		8: 'attackmove',
		9: 'holdposition',
		10: 'patrol',
		-1: 'garrison',
    }
    sensedistance = 1152.0
    attributes = ['medium']
    image_name = 'vgui/rebels/units/unit_rebel_tau'
    infest_zombietype = ''
	
class OverrunRebelHeavyInfo(RebelTauInfo):
	name = 'overrun_unit_rebel_tau'
	costs = [('kills', 4)]
	techrequirements = ['or_tier2_research']
	abilities = {
        #0: 'tau_alt_fire',
        #1: 'rebel_grenade_upgrade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
	}
	buildtime = 0
	
class RebelHeavyInfo(RebelInfo):
    name = 'unit_rebel_heavy'
    displayname = '#RebHeavy_Name'
    description = '#RebHeavy_Description'
    buildtime = 28.0
    maxspeed = 184
    health = 280
    viewdistance = 896
    scale = 1.10
    costs = [[('requisition', 70), ('scrap', 25)], [('kills', 2)]]
    accuracy = 0.625
    population = 2
    modelname = 'models/rebel_heavy.mdl'
    techrequirements = ['build_reb_techcenter']
    weapons = ['weapon_rebel_heavy_gun']
    abilities = {
        0: 'smokegrenade',
        #1: 'rebel_grenade_upgrade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    sensedistance = 1024.0
    attributes = ['heavy']
    image_name = 'vgui/rebels/units/unit_rebel_heavy'
    infest_zombietype = ''
	
class OverrunRebelHeavyInfo(RebelHeavyInfo):
	name = 'overrun_unit_rebel_heavy'
	costs = [('kills', 4)]
	techrequirements = ['or_tier2_research']
	abilities = {
        #0: 'smokegrenade',
        #1: 'rebel_grenade_upgrade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
	}
	buildtime = 0


class DestroyHQRebelAR2Info(RebelAR2Info):
    name = 'unit_rebel_ar2_destroyhq'
    techrequirements = ['build_reb_munitiondepot_destroyhq','weaponar2_unlock']


class RebelMedicInfo(RebelShared):
    name = 'unit_rebel_medic'
    cls_name = 'unit_rebel_medic'
    buildtime = 22.0
    maxspeed = 224
    viewdistance = 768
    unitenergy = 100
    costs = [[('requisition', 15), ('scrap', 10)], [('kills', 1)]]
    displayname = '#RebMedic_Name'
    description = '#RebMedic_Description'
    image_name = 'vgui/rebels/units/unit_rebel_medic'
    techrequirements = ['build_reb_triagecenter']
    modellist = GenerateModelList('MEDIC')
    attributes = ['medium']
    abilities = {
        0: 'heal',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['weapon_pistol']


class RebelMedicSmg1Info(RebelMedicInfo):
    name = 'unit_rebel_medic_smg1'
    weapons = ['weapon_smg1']
    displayname = '#RebMedicSmg1_Name'
    description = '#RebMedicSmg1_Description'
    techrequirements = []


class DestroyHQRebelMedicInfo(RebelMedicInfo):
    name = 'destroyhq_unit_rebel_medic'
    techrequirements = ['build_reb_triagecenter_destroyhq']

class DestroyHQRebelMedicSmg1Info(RebelMedicSmg1Info):
    name = 'destroyhq_unit_rebel_medic_smg1'
    techrequirements = ['build_reb_triagecenter_destroyhq']


class RebelEngineerInfo(RebelShared):
    name = 'unit_rebel_engineer'
    cls_name = 'unit_rebel_engineer'
    modelname = 'models/Humans/Group03/male_05_worker.mdl'
    buildtime = 15.0
    health = 50
    population = 1
    costs = [[('requisition', 15)], [('kills', 1)]]
    resource_category = 'economy'
    engagedistance = 500.0
    scrapdropchance = 0.0
    maxspeed = 180
    displayname = '#RebEngineer_Name'
    description = '#RebEngineer_Description'
    image_name = 'vgui/rebels/units/unit_rebel_engineer'
    #sound_select = 'unit_rebel_engineer_select'
    #sound_move = 'unit_rebel_engineer_move'
    #sound_attack = 'unit_rebel_engineer_attack'
    #tier = 1
    accuracy = 0.9
    viewdistance = 768
    abilities = {
        0: 'repair_dog',
        5: 'salvage',
        6: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct', #TODO: use a different construct function from Stalker, so we can repair Dog.
        -1: 'garrison',
        3: SubMenu(name='engie_defensemenu',
                   displayname='#RebDefenseMenu_Name', description='#RebDefenseMenu_Description',
                   image_name='vgui/abilities/building_defence_menu.vmt',
                   abilities={
                        0: 'build_reb_barricade',
                        1: 'rebels_mountableturret',
                        2: 'build_reb_barreltrap',
                        3: 'build_reb_bunker',
                        4: 'build_reb_aidstation',
                        5: 'build_reb_detectiontower',
                        6: 'build_reb_teleporter',
                        11: 'menuup',
                   }),
        7: SubMenu(name='engie_menu', displayname='#RebMenu_Name', description='#RebMenu_Description',
                   image_name='vgui/abilities/building_menu.vmt', abilities={
						0: 'build_reb_hq',
						1: 'build_reb_billet',
						2: 'build_reb_junkyard',
						4: 'build_reb_barracks',
						5: 'build_reb_specialops',
						6: 'build_reb_vortigauntden',
						7: 'build_reb_munitiondepot',
						8: 'build_reb_triagecenter',
						9: 'build_reb_techcenter',
						11: 'menuup',
                   })
    }
    weapons = ['weapon_hammer', 'weapon_pistol']
    sai_hint = set(['sai_unit_builder', 'sai_unit_salvager'])


class DestroyHQRebelEngineerInfo(RebelEngineerInfo):
    name = 'destroyhq_unit_rebel_engineer'
    abilities = {
        5: 'salvage',
        6: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
        -1: 'garrison',
        3: SubMenu(name='engie_defensemenu_destroyhq',
                   displayname='#RebDefenseMenu_Name', description='#RebDefenseMenu_Description',
                   image_name='vgui/abilities/building_defence_menu.vmt',
                   abilities={
                        0: 'build_reb_barricade_destroyhq',
                        1: 'destroyhq_reb_mountableturret',
                        2: 'build_reb_barreltrap_destroyhq',
                        3: 'build_reb_bunker_destroyhq',
                        4: 'build_reb_aidstation_destroyhq',
                        5: 'build_reb_detectiontower_destroyhq',
                        6: 'build_reb_teleporter_destroyhq',
                        11: 'menuup',
                   }),
        7: SubMenu(name='engie_menu_destroyhq', displayname='#RebMenu_Name', description='#RebMenu_Description',
                   image_name='vgui/abilities/building_menu.vmt', abilities={
						0: 'build_reb_hq_destroyhq',
						1: 'build_reb_billet_destroyhq',
						2: 'build_reb_junkyard_destroyhq',
						4: 'build_reb_barracks_destroyhq',
						5: 'build_reb_specialops_destroyhq',
						6: 'build_reb_vortigauntden_destroyhq',
						7: 'build_reb_munitiondepot_destroyhq',
						8: 'build_reb_triagecenter_destroyhq',
						9: 'build_reb_techcenter',
						11: 'menuup',
                   })
    }


class TutorialRebelEngineerInfo(RebelEngineerInfo):
    name = 'tutorial_rebel_engineer'
    abilities = {
        5: 'salvage',
        6: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
        -1: 'garrison',
        3: SubMenu(name='engie_defensemenu_tutorial',
                   displayname='#RebDefenseMenu_Name', description='#RebDefenseMenu_Description',
                   image_name='vgui/abilities/building_defence_menu.vmt',
                   abilities={
                        0: 'build_reb_barricade',
                        1: 'rebels_mountableturret',
                        2: 'build_reb_barreltrap',
                        3: 'build_reb_bunker',
                        4: 'build_reb_aidstation',
                        5: 'build_reb_detectiontower',
                        6: 'build_reb_teleporter',
                        11: 'menuup',
                   }),
        7: SubMenu(name='engie_menu_tutorial', displayname='#RebMenu_Name', description='#RebMenu_Description',
                   image_name='vgui/abilities/building_menu.vmt', abilities={
                        0: 'build_reb_hq',
                        1: 'build_reb_billet',
                        2: 'build_reb_junkyard_tutorial',
                        4: 'build_reb_barracks_tutorial',
                        5: 'build_reb_munitiondepot',
                        6: 'build_reb_specialops',
                        8: 'build_reb_triagecenter',
                        9: '	',
                        11: 'menuup',
                   })
    }


class RebelRPGUnlock(AbilityUpgrade):
    name = 'rebel_rpg_unlock'
    displayname = '#RebRPGUnlock_Name'
    description = '#RebRPGUnlock_Description'
    image_name = 'vgui/rebels/abilities/rebel_rpg_unlock'
    buildtime = 95.0
    costs = [('requisition', 50)]


class RebelRPGInfo(RebelShared):
    name = 'unit_rebel_rpg'
    buildtime = 30.0
    health = 240
    maxspeed = 160.0
    viewdistance = 896
    costs = [[('requisition', 60), ('scrap', 45)], [('kills', 4)]]
    displayname = '#RebRPG_Name'
    description = '#RebRPG_Description'
    image_name = 'vgui/rebels/units/unit_rebel_rpg'
    #tier = 3
    abilities = {
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['weapon_rpg']
    sensedistance = 1280.0
    techrequirements = ['build_reb_techcenter']
    population = 2
    attributes = ['medium', 'rpg']


class RebelVeteranUnlock(AbilityUpgrade):
    name = 'rebel_veteran_unlock'
    displayname = '#RebVeteranUnlock_Name'
    description = '#RebVeteranUnlock_Description'
    image_name = 'vgui/rebels/abilities/rebel_veteran_unlock'
    buildtime = 95.0
    costs = [('requisition', 50)]


@entity ('unit_rebel_veteran', networked=True)
class UnitCitizenBase(UnitCitizen):
    canshootmove = False
    insteadyposition = BooleanField(value=False, networked=True)

    def OnInCoverChanged(self):
        super().OnInCoverChanged()
        self.insteadyposition = self.in_cover

    if isserver:
        def Precache(self):
            super().Precache()

            self.PrecacheScriptSound("unit_rebel_hurt")
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionHideSpot(BaseClass.BehaviorGenericClass.ActionHideSpot):
                # Don't break cover when targeting an enemy
                def OnNewOrder(self, order):
                    if order.type == order.ORDER_ENEMY:
                        return self.SuspendFor(self.behavior.ActionHideSpotAttack, 'Attacking enemy on order from cover/hold spot', order.target)

    def OnTakeDamage(self, dmginfo):
        if self.lasttakedamage and self.health > 0 and dmginfo.GetDamage() > 0:

            self.EmitSound('unit_rebel_hurt')
        return super().OnTakeDamage(dmginfo)


class RebelVeteran(RebelShared):
    name = 'unit_rebel_veteran'
    cls_name = 'unit_rebel_veteran'
    buildtime = 35.0
    health = 180
    maxspeed = 192.0
    viewdistance = 896
    attributes = ['medium']
    costs = [[('requisition', 50), ('scrap', 50)], [('kills', 4)]]
    displayname = '#RebVeteran_Name'
    description = '#RebVeteran_Description'
    image_name = 'vgui/rebels/units/unit_rebel_crossbow'
    techrequirements = ['build_reb_specialops']
    #tier = 3

    abilities = {
        0: 'fireexplosivebolt',
        1: 'smokegrenade',
        2: 'rebel_steadyposition',
        3: 'crossbow_attack',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    #weapons = ['weapon_shotgun', 'weapon_ar2']
    weapons = ['weapon_crossbow']
    sensedistance = 1536.0
    #techrequirements = ['rebel_veteran_unlock']
    #accuracy = 'high'
    population = 2
    cantakecover = True


class DestroyHQRebelVeteran(RebelVeteran):
    name = 'destroyhq_unit_rebel_veteran'
    techrequirements = ['build_reb_munitiondepot_destroyhq']
    abilities = {
        0: 'fireexplosivebolt_destroyhq',
        1: 'smokegrenade',
        2: 'rebel_steadyposition',
        3: 'crossbow_attack',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class RebelFlamer(RebelShared):
    name = 'unit_rebel_flamer'
    #cls_name = 'unit_rebel_flamer' 
    cls_name = 'unit_rebel_csm'
    buildtime = 32.0
    health = 270
    maxspeed = 248.0
    viewdistance = 768
    scale = 1.075
    attributes = ['heavy']
    costs = [[('requisition', 50), ('scrap', 20)], [('kills', 3)]]
    modelname = 'models/Humans/Group03/male_05_flamer.mdl'
    displayname = '#RebFlamer_Name'
    description = '#RebFlamer_Description'
    image_name  = 'vgui/rebels/units/unit_rebel_flamer'
    #techrequirements = ['build_reb_munitiondepot']
    #tier = 3
    abilities = {
        0: 'smokegrenade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['wars_weapon_flamer']
    population = 2
    infest_zombietype = ''


# Transform abilities Rebel soldier
class TransformToRebelSG(AbilityTransformUnit):
    name = 'rebel_transform_sg'
    displayname = '#RebTransSG_Name'
    description = '#RebTransSG_Description'
    transform_type = 'unit_rebel_sg'
    transform_time = 5.0
    replaceweapons = True
    techrequirements = ['weaponsg_unlock']
    #techrequirements = ['build_reb_munitiondepot']
    costs = [('scrap', 5)]
    image_name = 'vgui/rebels/abilities/rebel_transform_sg'
    activatesoundscript = 'ability_combine_shotgun_upgrade'


class TransformToRebelAR2(AbilityTransformUnit):
    name = 'rebel_transform_ar2'
    displayname = '#RebTransAR2_Name'
    description = '#RebTransAR2_Description'
    transform_type = 'unit_rebel_ar2'
    transform_time = 5.0
    replaceweapons = True
    techrequirements = ['weaponar2_unlock']
    #techrequirements = ['build_reb_munitiondepot']
    costs = [('scrap', 10)]
    image_name = 'vgui/rebels/abilities/rebel_transform_ar2'
    activatesoundscript = 'ability_combine_ar2_upgrade'


class UnlockRebelTierMiddle (AbilityUpgrade):
    name = 'rebel_upgrade_tier_mid'
    displayname = '#RebUpTierMid_Name'
    description = '#RebUpTierMid_Description'
    buildtime = 60.0
    costs = [('requisition', 40), ('scrap', 10)]


# Medic upgrades
class MedicHealRateUpgrade(AbilityUpgradeValue):
    name = 'medic_healrate_upgrade'
    displayname = '#RebMedHealRateUpgr_Name'
    description = '#RebMedHealRateUpgr_Description'
    buildtime = 35.0
    costs = [('requisition', 25), ('scrap', 15)]
    upgradevalue = 75.0
    image_name = 'vgui/rebels/abilities/medic_healrate_upgrade'

class MedicEnergyRegenRateUpgrade(AbilityUpgradeValue):
    name = 'medic_regenerate_upgrade'
    displayname = '#MedEnRegRateUpgr_Name'
    description = '#MedEnRegRateUpgr_Description'
    buildtime = 35.0
    costs = [('requisition', 25), ('scrap', 15)]
    upgradevalue = 5.0
    image_name = 'vgui/rebels/abilities/medic_regenerate_upgrade'


class MedicMaxEnergyUpgrade(AbilityUpgradeValue):
    name = 'medic_maxenergy_upgrade'
    displayname = '#MedMaxEnUpgr_Name'
    description = '#MedMaxEnUpgr_Description'
    buildtime = 35.0
    costs = [('requisition', 25), ('scrap', 15)]
    upgradevalue = 150
    image_name = 'vgui/rebels/abilities/medic_maxenergy_upgrade'


class MedicSMG1Upgrade(AbilityUpgrade):
    name = 'medic_smg1_upgrade'
    displayname = '#MedSMG1Upgr_Name'
    description = '#MedSMG1Upgr_Description'
    buildtime = 38.0
    costs = [('requisition', 20), ('scrap', 15)]
    image_name = "vgui/rebels/abilities/medic_smg_upgrade"
    sai_hint = AbilityUpgrade.sai_hint | set(['sai_unit_unlock'])

    def OnUpgraded(self):
        super().OnUpgraded()

        self.UpgradeMedicInfo(RebelMedicInfo, RebelMedicSmg1Info)
        self.UpgradeMedicInfo(DestroyHQRebelMedicInfo, DestroyHQRebelMedicSmg1Info)

    def UpgradeMedicInfo(self, info, successor_info):
        # Ensure buildings producing this unit now produce the medic with smg1
        # The system is not made for this and so far this is only case we have.
        # So the code is pretty hacky.
        technode = GetTechNode(info.name, self.ownernumber)
        technode.researching = False
        technode.showonunavailable = False
        technode.successorability = successor_info.name
        technode.techenabled = False # This is a setter that detects changes, very hacky to set to False and then to True...
        technode.techenabled = True # Changing techenabled calls RecomputeAvailable

        # Create copy of unit list as calling SetUnitType will mutate the list
        units_to_upgrade = list(unitlistpertype[self.ownernumber][info.name])
        for unit in units_to_upgrade:
            unit.SetUnitType(successor_info.name)
            unit.RemoveAllWeapons()
            unit.EquipWeapons()

class OverrunRebelPartisanInfo(RebelPartisanInfo):
    name = 'overrun_unit_rebel_partisan'
    hidden = True
    tier = 0
    buildtime = 0


class OverrunRebelPartisanMolotovInfo(RebelPartisanMolotovInfo):
    name = 'overrun_unit_rebel_partisan_molotov'
    hidden = True
    tier = 0
    buildtime = 0


class OverrunRebelInfo(RebelInfo):
    name = 'overrun_unit_rebel'
    hidden = True
    buildtime = 0
    tier = 0
    techrequirements = []
    abilities = {
        0: 'overrun_grenade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class OverrunRebelSGInfo(RebelSGInfo):
    name = 'overrun_unit_rebel_sg'
    hidden = True
    buildtime = 0
    tier = 0
    techrequirements = ['or_tier2_research']
    abilities = {
        0: 'overrun_grenade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class OverrunRebelEngineerInfo(RebelEngineerInfo):
    name = 'overrun_unit_rebel_engineer'
    hidden = True
    buildtime = 0
    tier = 0
    abilities = {
        -2: 'construct_floorturret',
        -1: 'garrison',
        1: 'overrun_build_reb_bunker',
        2: 'overrun_floor_turret',
        3: 'overrun_combine_mine',
        4: 'overrun_build_reb_barricade',
        5: 'overrun_reb_mountableturret',
        6: 'overrun_build_reb_aidstation',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
    }


class OverrunRebelAR2Info(RebelAR2Info):
    name = 'overrun_unit_rebel_ar2'
    hidden = True
    buildtime = 0
    tier = 0
    techrequirements = ['or_tier2_research']
    abilities = {
        0: 'overrun_grenade',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class OverrunRebelFlamerInfo(RebelFlamer):
    name = 'overrun_unit_rebel_flamer'
    hidden = True
    buildtime = 0
    tier = 0
    techrequirements = ['or_tier2_research']
    abilities = {
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class OverrunRebelMedicInfo(RebelMedicInfo):
    name = 'overrun_unit_rebel_medic'
    hidden = True
    buildtime = 0
    tier = 0
    techrequirements = ['or_tier2_research']
    abilities = {
        0: 'heal',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }


class OverrunRebelRPGInfo(RebelRPGInfo):
    name = 'overrun_unit_rebel_rpg'
    hidden = True
    buildtime = 0
    techrequirements = ['or_tier3_research']
    accuracy = 5.0


class OverrunRebelVeteranInfo(RebelVeteran):
    name = 'overrun_unit_rebel_veteran'
    hidden = True
    buildtime = 0
    tier = 0
    techrequirements = ['or_tier3_research']
    abilities = {
        0: 'fireexplosivebolt_overrun',
        1: 'smokegrenade',
        2: 'rebel_steadyposition',
        3: 'crossbow_attack',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',

    }
    cantakecover = True

# Mission Versions
class MissionRebelInfo(RebelInfo):
    name = 'mission_unit_rebel'
    hidden = True
    maxspeed = 250.0
    viewdistance = 700
    health = 75
    scrapdropchance = 0.0
    buildtime = 0.5
    costs = [('requisition', 12)]
    techrequirements = []
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }

class MissionRebelSGInfo(RebelSGInfo):
    name = 'mission_unit_rebel_sg'
    hidden = True
    maxspeed = 250.0
    viewdistance = 700
    health = 70
    scrapdropchance = 0.0
    buildtime = 0.5
    costs = [('requisition', 15)]
    techrequirements = []
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }

class MissionRebelMedicInfo(RebelMedicInfo):
    name = 'mission_unit_rebel_medic'
    hidden = True
    maxspeed = 250.0
    viewdistance = 700
    health = 50
    unitenergy = 55
    unitenergy_initial = 0
    scrapdropchance = 0.0
    buildtime = 0.5
    costs = [('requisition', 18)]
    techrequirements = []
    abilities = {
        0: 'mission_heal',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = []

class MissionRebelSaboteurInfo(RebelSaboteurInfo):
    name = 'mission_unit_rebel_saboteur'
    hidden = False
    maxspeed = 250.0
    viewdistance = 700
    health = 40
    unitenergy = 30
    unitenergy_initial = 20
    scrapdropchance = 0.0
    buildtime = 0.5
    costs = [('requisition', 25)]
    techrequirements = ['build_reb_munitiondepot_mission']
    abilities = {
        0: 'mission_grenade',
        1: 'mission_smokegrenade',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = []

class MissionRebelFlamer(RebelFlamer):
    name = 'mission_unit_rebel_flamer'
    hidden = True
    health = 400
    maxspeed = 160.0
    viewdistance = 900
    abilities = {
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = ['wars_weapon_flamer']

class MissionRebelScoutInfo(RebelScoutInfo):
    name = 'mission_unit_rebel_scout'
    hidden = True
    maxspeed = 250.0
    viewdistance = 1000
    health = 30
    buildtime = 0.5
    costs = [('requisition', 20)]
    techrequirements = []
    abilities = {
        0: 'infiltrate',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    weapons = []

class MissionRebelPartisanMolotovInfo(RebelPartisanMolotovInfo):
    name = 'mission_unit_rebel_partisan_molotov'
    hidden = False
    maxspeed = 250.0
    viewdistance = 850
    health = 35
    scrapdropchance = 0.0
    buildtime = 0.5
    costs = [('requisition', 15)]
    techrequirements = []
    abilities = {
        0: 'throwmolotov',
        1: 'throwstinkbomb',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }

class MissionRebelEngineerInfo(RebelEngineerInfo):
    name = 'mission_unit_rebel_engineer'
    hidden = False
    maxspeed = 250.0
    viewdistance = 700
    health = 65
    buildtime = 0.5
    scrapdropchance = 0.0
    costs = [('requisition', 22)]
    techrequirements = []
    abilities = {
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
        7: SubMenu(name='mission_engie_menu', displayname='#RebMenu_Name', description='#RebMenu_Description',  image_name = 'vgui/abilities/building_menu.vmt', abilities={
            0: 'build_reb_shack',
            4: 'build_reb_barreltrap_mission',
            11: 'menuup',
        })
    }
    weapons = ['weapon_hammer']

# ======================================================================================================================
# ============================================================ Character Units =========================================
# ======================================================================================================================


#  TODO: Make it properly


@entity('char_rebel_flamer')
class UnitCharRebelFlamer(UnitRebel):
    pass


@entity('char_rebel_soldier', networked=True)
class CharacterUnitCanShootMove(UnitCitizen):
    if isserver:
        def Precache(self):
            super().Precache()

            self.PrecacheScriptSound("unit_rebel_hurt")

    def OnTakeDamage(self, dmginfo):
        if self.lasttakedamage and self.health > 0 and dmginfo.GetDamage() > 0:

            self.EmitSound('unit_rebel_hurt')
        return super().OnTakeDamage(dmginfo)

    # Settings
    canshootmove = True


@entity('char_rebel_medic', networked=True)
class CharacterRebelMedicUpgradeHealth(UnitRebel):
    if isserver:
        def Precache(self):
            super().Precache()

            PrecacheParticleSystem(self.rangerangeparticlename)

        def Spawn(self):
            super().Spawn()

            zmin = self.WorldAlignMins().z
            zmax = self.WorldAlignMaxs().z
            origin = self.GetAbsOrigin()
            origin.z += zmin

            self.healarea = CreateEntityByName('trigger_heal_area')
            self.healarea.startdisabled = True
            self.healarea.SetOwnerNumber(self.GetOwnerNumber())
            UTIL_SetOrigin(self.healarea, origin)
            UTIL_SetSize(self.healarea, -Vector(self.healradius, self.healradius, -zmin),
                         Vector(self.healradius, self.healradius, zmax))
            DispatchSpawn(self.healarea)
            self.healarea.SetOwnerEntity(self)
            self.healarea.SetParent(self)
            self.healarea.Activate()
            self.UpdateHealAreaState()

            if self.healarea:
                self.ishealing = self.healarea.healing

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            if self.healarea:
                UTIL_Remove(self.healarea)

    def UpdateHealAreaState(self):
        if self.healarea:
            if self.health <= 0:
                self.healarea.Disable()
            else:
                self.healarea.Enable()

    if isclient:
        def Spawn(self):
            super().Spawn()

            self.EnableRangeRadiusOverlay()

        def UpdateOnRemove(self):
            super().UpdateOnRemove()

            self.EnableRangeRadiusOverlay()

        def EnableRangeRadiusOverlay(self):
            if self.rangerangeoverlay:
                return
            mins = self.CollisionProp().OBBMins()
            range = self.healradius
            self.rangerangeoverlay = self.ParticleProp().Create(self.rangerangeparticlename, PATTACH_ABSORIGIN_FOLLOW,
                                                                -1, Vector(0, 0, mins.z))
            self.rangerangeoverlay.SetControlPoint(4, self.GetTeamColor())
            self.rangerangeoverlay.SetControlPoint(2, Vector(range, 0, 0))

        def DisableRangeRadiusOverlay(self):
            if not self.rangerangeoverlay:
                return
            self.ParticleProp().StopEmission(self.rangerangeoverlay, False, False, True)
            self.rangerangeoverlay = None

        def OnSelected(self, player):
            super().OnSelected(player)

            self.DisableRangeRadiusOverlay()

        def OnDeSelected(self, player):
            super().OnDeSelected(player)

            self.EnableRangeRadiusOverlay()

    healarea = None
    healradius = 192

    rangerangeparticlename = 'range_radius_health'
    rangerangeoverlay = None

    # Settings
    maxheal = UpgradeField(value=100.0, abilityname='char_level_1')


@entity('character_unit')
class CharacterUnit(UnitRebel):
    pass

    # Settings
    # canshootmove = True


class CharacterRebelSoldier(RebelInfo):
    name = 'char_rebel_soldier'
    cls_name = 'char_rebel_soldier' # can shoot while running
    displayname = '#CharRebSoldier_Name'
    description = '#CharRebSoldier_Description'
    techrequirements = []
    maxspeed = 250
    viewdostance = 850
    health = 1000
    buildtime = 0.01
    scrapdropchance = 1.0
    accuracy = 1.3
    costs = []
    population = 1
    attributes = ['assault']
    tier = 0
    weapons = ['weapon_smg1_sw']
    #weapons = ['weapon_smg1_char']
    abilities = {
        0: 'grenade_soldier',
        1: 'stun_frag',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0


class CharacterRebelFlamer(UnitRebel):
    name = 'char_rebel_flamer'
    cls_name = 'char_rebel_flamer' # so that flamer doesn't explode when shot in the back
    displayname = '#CharRebFlamer_Name'
    description = '#CharRebFlamer_Description'
    maxspeed = 210
    viewdistance = 700
    health = 1200
    buildtime = 0.01
    scrapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['tank']
    tier = 0
    abilities = {
        0: 'smokegrenade_char',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0


class CharacterRebelMedic(RebelMedicInfo):
    name = 'char_rebel_medic'
    cls_name = 'char_rebel_medic'
    displayname = '#CharRebMedic_Name'
    description = '#CharRebMedic_Description'
    maxspeed = 250
    viewdistance = 800
    maxenergy = 300
    techrequirements = []
    health = 1100
    buildtime = 0.01
    scrapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['medic']
    tier = 0
    abilities = {
        0: 'heal_char',
        1: 'passivehealing_indicator',
        2: 'stun_frag',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        -1: 'garrison',
    }
    weapons = ['weapon_smg1']
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0
# TODO: buff the  abilities


class CharacterRebelEngineer(RebelEngineerInfo):
    name = 'char_rebel_engineer'
    displayname = '#CharRebEngineer_Name'
    description = '#CharRebEngineer_Description'
    maxspeed = 250
    viewdistance = 800
    health = 900
    buildtime = 0.01
    scrapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['support']
    tier = 0
    abilities = {
        5: 'salvage',
        6: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
        11: 'construct',
        3: SubMenu(name='engie_defensemenu_char', displayname='#RebDefenseMenu_Name', description='#RebDefenseMenu_Description',
                   image_name='vgui/abilities/building_menu.vmt', abilities={
                        0: 'build_char_barricade',
                        1: 'char_mountableturret', #TODO: allow to be used by all members
                        2: 'build_reb_char_barreltrap',
                        11: 'menuup',
                   })
    }
    weapons = ['weapon_hammer', 'weapon_shotgun']
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0

class CharacterRebelVeteran(RebelVeteran):
    name = 'char_rebel_veteran'
    displayname = '#CharRebVeteran_Name'
    description = '#CharRebVeteran_Description'
    maxspeed = 250
    viewdistance = 900
    health = 800
    buildtime = 0.01
    scrapdropchance = 1.0
    techrequirements = []
    costs = []
    population = 1
    attributes = ['dps']
    tier = 0
    weapons = ['weapon_crossbow']
    abilities = {
        0: 'fireexplosivebolt_char',
        1: 'rebel_steadyposition',
        2: 'crossbow_attack',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0

class CharacterRebelScout(RebelScoutInfo):
    name = 'char_rebel_scout'
    displayname = '#CharRebScout_Name'
    description = '#CharRebScout_Description'
    maxspeed = 300
    viewdistance = 1024
    health = 900
    unitenergy = 50
    buildtime = 0.01
    srapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['scout']
    tier = 0
    weapons = ['weapon_smg1']
    abilities = {
        0: 'infiltrate_char',
        1: 'stab',
        2: 'c4explosive_char',
        #2: 'impale_char',
        7: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0

class CharacterRebelRPG(RebelRPGInfo):
    name = 'char_rebel_rpg'
    displayname = '#CharRebRPG_Name'
    description = '#CharRebRPG_Description'
    maxspeed = 230
    viewdistance = 800
    health = 1000
    buildtime = 0.01
    scrapdropchance = 1.0
    costs = []
    population = 1
    attributes = ['support']
    tier = 0
    abilities = {
        0: 'char_throwstinkbomb',  # TODO
        6: 'mountturret',
        8: 'attackmove',
        9: 'holdposition',
        10: 'patrol',
    }
    recharge_other_abilities = {
        'char_combine_soldier',
        'char_combine_elite',
        'char_metropolice_support',
        'char_metropolice_tank',
        'char_metropolice_scout',
        'char_rebel_scout',
        'char_rebel_flamer',
        'char_rebel_veteran',
        'char_rebel_rpg',
        'char_rebel_engineer',
        'char_rebel_medic',
        'char_rebel_soldier',
    }
    rechargetime = 180.0


class UnitRebelTest(RebelInfo): # just a test for the new weapon for Squad Wars
                                # TODO: find where weapon data file is located
    name = 'unit_rebel_test'
    weapons = ['weapon_smg1_sw']