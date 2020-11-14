from entities import CPointEntity, entity, entitylist, GetClassByClassname
from fields import input, PlayerField, IntegerField, BooleanField, fieldtypes, input
if isserver:
    from core.strategicai import EnableStrategicAI, DisableStrategicAI

@entity('wars_cpu_player',
        base=['Targetname', 'Parentname', 'Angles'],
        iconsprite='editor/wars_cpu_player.vmt')
class EntCPUPlayer(CPointEntity):
    @input(inputname='EnableCPUPlayer', helpstring='Enables the CPU Player')
    def InputEnableCPUPlayer(self, inputdata):
        difficulty = None
        difficultyent = entitylist.FindEntityByClassname(None, 'wars_sp_difficulty')
        if difficultyent:
            difficulty = difficultyent.difficulty
        else:
            difficultycls = GetClassByClassname('wars_sp_difficulty')
            assert difficultycls != None, 'wars_sp_difficulty should exist'
            if difficultycls:
                difficulty = difficultycls.GetPlayerDefaultDifficulty() # Note: might still be none, but will default to medium
        
        EnableStrategicAI(self.cpuplayer, difficulty=difficulty)
        
    @input(inputname='DisableCPUPlayer', helpstring='Disables the CPU Player')
    def InputDisableCPUPlayer(self, inputdata):
        DisableStrategicAI(self.cpuplayer)
        
    cpuplayer = PlayerField(keyname='CPUPlayer', displayname='CPU Player',helpstring='Target CPU player to be enabled or disabled' )