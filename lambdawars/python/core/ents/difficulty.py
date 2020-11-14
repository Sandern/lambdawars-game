'''
Created on 26.08.2013
Triggers the selected difficulty for singleplayer.

@author: ProgSys
'''

if isserver:
    from entities import CBaseEntity, entity, entitylist
    from fields import StringField, IntegerField, BooleanField, OutputField, input, fieldtypes
    import matchmaking
    from gameinterface import ConVar, FCVAR_CHEAT
    
    wars_difficulty_override = ConVar('wars_difficulty_override', '', FCVAR_CHEAT)
    
    @entity('wars_sp_difficulty',
            base=[],
            iconsprite='editor/wars_sp_difficulty.vmt')
    class WarsSpDifficulty(CBaseEntity):
        # Outputs
        onspawn = OutputField(keyname='OnSpawn')
        onspawneasy = OutputField(keyname='OnSpawnEasy')
        onspawnnormal = OutputField(keyname='OnSpawnNormal')
        onspawnhard = OutputField(keyname='OnSpawnHard')
        
        ontrigger = OutputField(keyname='OnTrigger')
        ontriggereasy = OutputField(keyname='OnTriggerEasy')
        ontriggernormal = OutputField(keyname='OnTriggerNormal')
        ontriggerhard = OutputField(keyname='OnTriggerHard')

        defaultdifficulty = StringField(value='Normal', keyname='Defaultdifficulty',
                                        displayname='Default Difficulty',
                                        helpstring='Default Difficulty (Easy,Normal or Hard). Used if the difficulty setting was not found.',
                                        choices=[('Normal', 'Normal'),('Easy', 'Easy'),('Hard', 'Hard')])
                                        
        difficulty = StringField(value=None)
        
        def Activate(self):
            super().Activate()
            
            self.onspawn.FireOutput(self, self)
            self.ApplyDifficulty(True)
        
        @input(inputname='Trigger', helpstring='Trigger the entity')
        def Trigger(self, inputdata):
            self.ontrigger.FireOutput(self, self)
            self.ApplyDifficulty(False)
            
        @classmethod
        def GetPlayerDefaultDifficulty(self):
            ''' Returns the player chosen difficulty (if any). '''
            overridediff = wars_difficulty_override.GetString()
            if overridediff:
                return overridediff
            elif matchmaking.IsSessionActive():
                return matchmaking.matchsession.GetSessionSettings().GetString('game/difficulty')
                
            return None
            
        def ApplyDifficulty(self, spawn):
            playerdefaultdiff = self.GetPlayerDefaultDifficulty()
            if playerdefaultdiff != None:
                self.DifficultyDecision(playerdefaultdiff, spawn)
            else:
                self.DifficultyDecision(self.defaultdifficulty, spawn)
        
        def DifficultyDecision(self, difficulty, spawn):
            difficulty = difficulty.lower()
            self.difficulty = difficulty
            DevMsg(1, "Difficulty Entity: %s\n" % difficulty)
            if spawn:
                if difficulty == 'easy':
                    self.onspawneasy.FireOutput(self, self)
                elif difficulty == 'hard':
                    self.onspawnhard.FireOutput(self, self)
                elif difficulty == 'normal':
                    self.onspawnnormal.FireOutput(self, self)
                else:
                    self.onspawnnormal.FireOutput(self, self)
                    PrintWarning('DifficultyDecision.Unknown difficulty %s, defaulting to Normal\n' % (difficulty))
            else:
                if difficulty == 'easy':
                    self.ontriggereasy.FireOutput(self, self)
                elif difficulty == 'hard':
                    self.ontriggerhard.FireOutput(self, self)
                elif difficulty == 'normal':
                    self.ontriggernormal.FireOutput(self, self)
                else:
                    self.ontriggernormal.FireOutput(self, self)
                    PrintWarning('DifficultyDecision.Unknown difficulty %s, defaulting to Normal\n' % (difficulty))
                    