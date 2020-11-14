from core.gamerules import GamerulesInfo, WarsBaseGameRules

class ExampleGameRules(WarsBaseGameRules):
    pass

class ExampleInfo(GamerulesInfo):
    name = 'example'
    displayname = 'Example Gamerules'
    description = 'Example Gamerules description.'
    cls = ExampleGameRules
    useteams = False