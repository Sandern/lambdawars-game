""" Overrun game mode related entities. """

if isserver:
    from entities import CPointEntity, entity
    from fields import input, OutputField, BooleanField, FloatField, IntegerField, StringField, FlagsField, fieldtypes, input
    from gamerules import gamerules
    from unit_helper import UnitBasePath, GOALTYPE_TARGETENT, GF_REQTARGETALIVE
    
    @entity('overrun_wave_spawnpoint',
            base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
            iconsprite='editor/overrun_wave_spawnpoint.vmt')
    class OverrunWaveSpawnPoint(CPointEntity):
        def __init__(self):
            super(OverrunWaveSpawnPoint, self).__init__()
            
            self.precomputedpaths = {}
    
        @input(inputname='Enable')
        def InputEnable(self, inputdata):
            self.disabled = False
            
        @input(inputname='Disable')
        def InputDisable(self, inputdata):
            self.disabled = True
            
        def GetPrecomputedPath(self, unit, target):
            ''' Gets a precomputed path for unittype to target.
                Calculates the path if it does not exists yet.
                Target should be a building. 
                
                This method assumes the unit was spawned near this point!
                
                Args:
                    unit (entity): Unit for which to get a path
                    target (entity): Goal entity of unit
            '''
            # See if we already have the precomputed path for this combination
            key = (unit.GetUnitType(), target)
            path = self.precomputedpaths.get(key, None)
            if path and (gpGlobals.curtime - path.timestamp) < 60.0:
                return path
                
            # Don't have it yet, so calculate the path
            destination = target.GetAbsOrigin()
            path = unit.navigator.FindPathAsResult(GOALTYPE_TARGETENT, destination, 32.0, GF_REQTARGETALIVE)
            path.timestamp = gpGlobals.curtime
            
            # Add new path and return a copy
            self.precomputedpaths[key] = path
            return UnitBasePath(self.precomputedpaths[key])
            
        disabled = BooleanField(value=False, keyname='StartDisabled')
        priority = IntegerField(value=0, keyname='Priority')
        maxradius = FloatField(value=0, keyname='MaxRadius', helpstring='Max spawn radius. 0 for default.')
    
    @entity('overrun_manager',
            base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
            iconsprite='editor/overrun_manager.vmt')
    class OverrunManager(CPointEntity):
        def Spawn(self):
            super(OverrunManager, self).Spawn()
            
            if self.GetSpawnFlags() & self.SF_CUSTOM_CONDITIONS:
                self.usecustomconditions = True
            
        def OnNewWave(self, wave):
            self.onnewwave.Set(wave, self, self)
        
        def WaveTypeDecision(self,wavetype):
            #print "WaveType: " +wavetype
            if wavetype == 'antlions':
                self.onantlions.FireOutput(self, self)
            elif wavetype == 'zombie':
                self.onzombies.FireOutput(self, self)
            elif wavetype == 'combine':
                self.oncombine.FireOutput(self, self)
            elif wavetype == 'rebels':
                self.onrebels.FireOutput(self, self)
        
        def DifficultyDecision(self,difficulty):
            #print "Difficulty: " +difficulty
            if difficulty == 'easy':
                self.oneasy.FireOutput(self, self)
            elif difficulty == 'normal':
                self.onnormal.FireOutput(self, self)
            elif difficulty == 'hard':
                self.onhard.FireOutput(self, self)
                        
        @input(inputname='Victory')
        def InputVictory():
            gamerules.EndOverrun()
            
        @input(inputname='Failed')
        def InputFailed():
            pass
            
        onnewwave = OutputField(keyname='OnNewWave', fieldtype=fieldtypes.FIELD_INTEGER)
        onantlions = OutputField(keyname='OnAntlions')
        onzombies = OutputField(keyname='OnZombies')
        oncombine = OutputField(keyname='OnCombine')
        onrebels = OutputField(keyname='OnRebels')
        
        oneasy= OutputField(keyname='OnEasy')
        onnormal = OutputField(keyname='OnNormal')
        onhard = OutputField(keyname='OnHard')
        
        indoor = BooleanField(value=False, keyname='InDoor', helpstring='Determines if this map is indoor')
        
        usecustomconditions = False
        wavetype = StringField(value='', keyname='wavetype')
        
        spawnflags = FlagsField(keyname='spawnflags', flags=
            [('SF_CUSTOM_CONDITIONS', ( 1 << 0 ), False)], 
            cppimplemented=True)
        
    @entity('overrun_distribution')
    class OverrunDistribution(CPointEntity):
        def __init__(self):
            super(OverrunDistribution, self).__init__()
            
            self.entries = []
            
        @input(inputname='AddEntry')
        def InputAddEntry():
            pass
        
    @entity('overrun_distribution_entry')
    class OverrunDistributionEntry(CPointEntity):
        unittype = StringField(value='', keyname='unittype')
        weight = FloatField(value=0.0, keyname='weight')
        
    @entity('overrun_headcrabcannister_spawnpoint',
            base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
            iconsprite='editor/overrun_headcrabcannister_spawnpoint.vmt')
    class OverrunHeadcrabCannisterSpawnPoint(CPointEntity):
        @input(inputname='Enable')
        def InputEnable(self, inputdata):
            self.disabled = False
            
        @input(inputname='Disable')
        def InputDisable(self, inputdata):
            self.disabled = True
            
        disabled = BooleanField(value=False, keyname='StartDisabled')
        maxradius = FloatField(value=1024, keyname='MaxRadius')
