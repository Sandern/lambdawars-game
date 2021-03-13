from vmath import Vector, QAngle
from core.buildings import WarsBuildingInfo, UnitBaseFactory as BaseClass
from entities import entity
from particles import PATTACH_POINT_FOLLOW

if isserver:
    from particles import PrecacheParticleSystem, DispatchParticleEffect
    
@entity('build_reb_munitiondepot', networked=True)
class RebelsMunitionDepot(BaseClass):
    if isclient:
        def OnBuildStateChanged(self):
            super(RebelsMunitionDepot, self).OnBuildStateChanged()
            
            if self.isproducing:
                self.StartSmoke()
            else:
                self.StopSmoke()
                
        def StartSmoke(self):
            if not self.steamfx01:
                self.steamfx01 = self.ParticleProp().Create("pg_steam", PATTACH_POINT_FOLLOW, 'steam01')
            if not self.steamfx02:
                self.steamfx02 = self.ParticleProp().Create("pg_steam", PATTACH_POINT_FOLLOW, 'steam02')
            
        def StopSmoke(self):
            if self.steamfx01:
                self.ParticleProp().StopEmission(self.steamfx01)
                self.steamfx01 = None
            if self.steamfx02:
                self.ParticleProp().StopEmission(self.steamfx02)
                self.steamfx02 = None  
    else:
        def DestructThink(self):
            super(RebelsMunitionDepot, self).DestructThink()
            #team color would be nice but no idear how to add it
            DispatchParticleEffect("goo_splash", PATTACH_POINT_FOLLOW, self, "glass01" )
            DispatchParticleEffect("goo_splash", PATTACH_POINT_FOLLOW, self, "glass02" )
            
        def Precache(self):
            super(RebelsMunitionDepot, self).Precache()
            
            PrecacheParticleSystem( "goo_splash" )
            PrecacheParticleSystem( "pg_steam" )

    # Effects
    steamfx01 = None
    steamfx02 = None
    # Settings
    autoconstruct = False
    buildtarget = Vector(0, -280, 32)
    buildangle = QAngle(0, 0, 0)
    rallylineenabled = False
    customeyeoffset = Vector(0,0,60)
    
# Register unit
class MuntionDepotInfo(WarsBuildingInfo):
    name = "build_reb_munitiondepot"
    displayname = "#BuildRebMunDepot_Name"
    description = "#BuildRebMunDepot_Description"
    cls_name = "build_reb_munitiondepot"
    image_name = 'vgui/rebels/buildings/build_reb_munitiondepot'
    modelname = 'models/pg_props/pg_buildings/rebels/pg_armory.mdl'
    explodemodel = 'models/pg_props/pg_buildings/rebels/pg_armory_des.mdl'
    costs = [('requisition', 50), ('scrap', 25)]
    resource_category = 'technology'
    health = 750
    buildtime = 56.0
    techrequirements = ['build_reb_barracks']
    abilities = {
        0: 'grenade_unlock',
        #1: 'rebel_upgrade_tier_mid',
        #1: 'combine_mine_unlock',
        #1: 'c4explosive_unlock',
        #2: 'rebel_mine_unlock',
        1: 'weaponsg_unlock',
        2: 'weaponar2_unlock',
        4: 'fireexplosivebolt_unlock',

        #4: 'dog_unlock',
        8: 'cancel',
        #10: 'rebel_rpg_unlock',
        #11: 'rebel_veteran_unlock',
    } 
    idleactivity = 'ACT_IDLE'
    workactivity = 'ACT_WORK'
    explodeactivity = 'ACT_EXPLODE'
    constructionactivity = 'ACT_CONSTRUCTION'
    sound_work = 'rebel_munitions_working' #'ATV_engine_idle'
    sound_select = 'build_reb_munitiondepot'
    sound_death = 'build_generic_explode1'
    explodeparticleeffect = 'pg_rebel_barracks_explosion'
    explodeshake = (2, 10, 2, 512) # Amplitude, frequence, duration, radius
    sai_hint = WarsBuildingInfo.sai_hint | set(['sai_building_research'])

class DestroyHQMuntionDepotInfo(MuntionDepotInfo):
    name = "build_reb_munitiondepot_destroyhq"
    techrequirements = ['build_reb_barracks_destroyhq']
	
# Mission version
class MissionMuntionDepotInfo(MuntionDepotInfo):
    name = "build_reb_munitiondepot_mission" 
    costs = [('requisition', 40)]
    health = 300
    buildtime = 15
    abilities = {}
