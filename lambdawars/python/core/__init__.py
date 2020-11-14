from . import signals
from gamedb import RegisterGamePackage
from gameinterface import engine

# Register our game package
RegisterGamePackage(
    name=__name__,
    dependencies=['srctests'],
    modules=[
        'statuseffects',
        'attributes',
        
        # Base Ability classes
        'abilities.info',
        'abilities.base',
        'abilities.menu',
        'abilities.instant',
        'abilities.cancel',
        'abilities.cancelupgrade',
        'abilities.mouseoverride',
        'abilities.target',
        'abilities.placeobject',
        'abilities.upgrade',
        'abilities.buildingupgrade',
        'abilities.attackmove',
        'abilities.holdposition',
        'abilities.patrol',

        'abilities.ungarrisonall',
        'abilities.throwobject',
        'abilities.jump',
        'abilities.ability_as_attack',
        'abilities.ability_as_animation',
        'abilities.debugnavdist',
        'abilities',
        
        # Factions
        'factions',
        
        # Hud
        '$ui.winlosedialog',
        '$ui.resourcesdialog',
        '$ui.statusplayers',
        '$ui.objectives',
        '$ui.messageboxdialog',
        '$ui.topbar',
        '$ui.chat',
        '$ui.waitingforplayers',
        'ui',
        
        # Units
        'units.cover',
        'units.info',
        'units.base',
        
        '$units.rallyline',
        'units.orders',
        'units.animstate',
        'units.locomotion',
        
        '#units.navigator_shared',
        '#units.navigator',
        '#units.senses',
        '#units.intention',
        '#units.behavior_generic',
        '#units.behavior_overrun',
        '#units.behavior_roaming',
        
        'units.basecombat',
        'units.basehuman',
        'units.baseobject',
        'units.basevehicle',
        'units.damagecontroller',
        'units',

        # Abilities depending on unit code
        'units.abilities.unittransform',
        'units.abilities.switchweapon',
        'units.abilities',

        # Weapons
        'weapons.base',
        'weapons.base_machinegun',
        'weapons.base_melee',
        'weapons.flamer_projectile',
        'weapons.flamer',
        'weapons',
        
        # Hud
        '$hud.info',
        '$hud.abilitybutton',
        '$hud.infobox',
        '$hud.notifier',
        '$hud.groups',
        '$hud.resourceindicator',
        '$hud.abilities',
        '$hud.units',
        '$hud.buildings',
        '$hud.minimap',
        '$hud.player_names',
        '$hud.cunit_display',
        'hud',


        # Notifications system
        'notifications',
        
        # Gamerules
        'gamerules.info',
        '#gamerules.statistics_collector',
        'gamerules.statistics_uploader',
        'gamerules.base',
        'gamerules.sandbox',
        'gamerules.mission',
        'gamerules',
        
        # Buildings
        'buildings.base',
        'buildings.dummy',
        'buildings.basefactory',
        'buildings.basegarrisonable',
        'buildings.func',
        'buildings.baseturret',
        'buildings.baseautoturret',
        'buildings.basemountableturret',
        'buildings',
        
        # Strategic AI
        '#strategicai.info',
        '#strategicai.groups',
        '#strategicai.abilityrules',
        '#strategicai.base',
        '#strategicai',

        # Entities
        '#ents.unitmaker',
        'ents.triggers',
        'ents.homingprojectile',
        'ents.event_building_listener',
        'ents.filters',
        'ents.giveresources',
        'ents.genericitem',
        'ents.followentity',
        'ents.messagebox',
        'ents.mission',
        'ents.navblocker',
        'ents.playerrelation',
        'ents.playersetup',
        'ents.cpuplayer',
        'ents.difficulty',
        'ents.giveorder',
        'ents.giveorder_random',
        'ents.abilities',
        'ents.musiccontroller',
        'ents.population_listener',
        'ents.mapboundary',
        '#ents.triggerarea',
        'ents.throwable_object',
        'ents',
        
        # Small system for controlling attributes/fields in Sandbox using the attribute editor
        'attributemgr',
        'attributemgr_shared',
        
        # Editor system
        'editor.*',
        'editor.tools.placetool',
        'editor.tools.*',
        '$editor.ui.*',

        # Utils
        '#util.techtree2dot',
        '#util.genfgd',
        '$util.genimagestub',
        '$util.genstats',
        'util.locomotion',
        'util.gamepackage',
        '#util.balancetester.reporter',
        '#util.balancetester.balancetest',
        '#util.balancetester.runner',
        '#util.balancetester.*',
        'units',
        'util',
        
        # Unit Tests
        'tests.units',
        'tests.*',
    ]
)  

def LoadGame(*args, **kwargs):
    # Set vars for consolespace module (module space for "py_run... " )
    from core.units import unitlist, unitlistpertype
    import consolespace
    
    consolespace.unitlist = unitlist
    consolespace.unitlistpertype = unitlistpertype
    
if isserver:
    def ApplyGameSettings(settings):
        from core.gamerules import SetNextLevelGamerules
        
        game = settings.get('game', {})
        mode = game.get('mode', None)
        map = settings.get('map', {})
        
        mapcommand = map.get('mapcommand', 'changelevel')
        
        if mode == 'mission':
            mission = game.get('mission', 'gamelobby')
            
            SetNextLevelGamerules('mission')
            engine.ServerCommand('%s %s reserved\n' % (mapcommand, mission))
            
            return True
