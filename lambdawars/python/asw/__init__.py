from gamemgr import RegisterGamePackage
from srcbase import DMG_BULLET
from gamerules import GetAmmoDef, BULLET_IMPULSE

particles=[
    # From HL2
    'particles/error.pcf',
    'particles/antlion_blood.pcf',
    'particles/blood_impact.pcf',
    'particles/water_impact.pcf',
    'particles/vortigaunt_fx.pcf',
    'particles/rocket_fx.pcf',
    'particles/weapon_fx_hl2.pcf',
    'particles/burning_fx.pcf',
    'particles/fire_01.pcf',
    #'particles/combineball.pcf',

    '!particles/fire_fx.pcf',
    '!particles/infested_blood.pcf',
    '!particles/infested_damage.pcf',

    'particles/ElevatorShaftFire.pcf',
    'particles/largesteamjet.pcf',
    'particles/VindIncendGrenade.pcf',
    'particles/mortarbug_fx.pcf',
    'particles/tracer_fx.pcf',
    'particles/impact_fx.pcf',
    '!particles/asw_weapon_fx.pcf',
    '!particles/sentry_fx.pcf',
    'particles/rain_fx.pcf',
    '!particles/boomer_fx.pcf',
    '!particles/asw_muzzle_fx.pcf',
    '!particles/asw_tracer_fx.pcf',
    '!particles/electrical_fx.pcf',
    'particles/explosion_fx.pcf',
    '!particles/buff_medic_fx.pcf',
    '!particles/buffgrenade_fx.pcf',
    'particles/asw_welding_fx.pcf',
    'particles/freeze_fx.pcf',
    'particles/asw_precipitation.pcf',
    'particles/ranger_fx.pcf',  
    'particles/shieldbug_fx.pcf',
    '!particles/buff_fx.pcf',
    'particles/smoke_fx.pcf',
    '!particles/asw_order_fx.pcf',
    'particles/asw_environmental_fx.pcf',
    'particles/asw_spark_fx.pcf',
    '!particles/footprint_fx.pcf',
    'particles/powerup_fx.pcf',
    '!particles/melee_fx.pcf',
    'particles/egg_fx.pcf',
    'particles/buzzer_fx.pcf',
    'particles/starfield.pcf',
    'particles/jumpjet_fx.pcf',
]
        
RegisterGamePackage(
        name=__name__,
        dependencies=['core'],
        #particles=particles,
        modules = [
            'ents.*',
            'units.*',
            'weapons.*',
        ],
)  

def LoadGame(*args, **kwargs):
    """ Called on 'load_gamepackage asw' """
    TRACER_LINE_AND_WHIZ = 4
    GetAmmoDef().AddAmmoType("ASW_R", DMG_BULLET, TRACER_LINE_AND_WHIZ, 10, 10, 40, BULLET_IMPULSE(200, 1225), 0 )
    GetAmmoDef().AddAmmoType("ASW_R_G", DMG_BULLET, TRACER_LINE_AND_WHIZ, 10, 10, 40, BULLET_IMPULSE(200, 1225), 0 )
    GetAmmoDef().AddAmmoType("ASW_F", DMG_BULLET, TRACER_LINE_AND_WHIZ, 10, 10, 40, BULLET_IMPULSE(200, 1225), 0 )
    