from gamemgr import RegisterGamePackage

__all__ = ['gamerules']
if isclient:
    __all__ += ['hud']
    
RegisterGamePackage(
    name=__name__,
    dependencies=['core'],
    modules=[
        'statuseffects',
        'attributes',
        'resources',
        'factions',
        'notifications',
        'achievements',
    
        # Hud
        '$hud.warshud',
        '$hud.*',
        
        # Ents
        'ents.*',
        
        # Abilities
        'abilities.powers.*',
        'abilities.steadyposition',
        'abilities.riot_station',
        'abilities.*',
        
        # Buildings
        'buildings.pheromone_marker',
        'buildings.dynmountableturret',
        'buildings.basebarricade',
        'buildings.neutral_barricade',
        'buildings.baseregeneration',
        'buildings.combine.basepowered',
        'buildings.combine.*',
        'buildings.rebels.*',
        'buildings.*',
        
        # Weapons
        'weapons.*',
        
        # Units
        'units.basezombie',
        'units.basehelicopter',
        'units.citizen',
        'units.*',
        
        # Gamerules
        'gamerules.*',
        
        # Strategic AI
        '#strategicai',
        
        # Singleplayer special cases
        'singleplayer.*',
    ]
)  
