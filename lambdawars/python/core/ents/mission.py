from entities import CBaseEntity, entity
from fields import LocalizedStringField, IntegerField, BooleanField, FloatField, OutputField, input, fieldtypes, GetField
from gamerules import gamerules
from core.decorators import clientonly_assert

if isclient:
    from core.ui import objectivespanel
else:
    from entities import FL_EDICT_ALWAYS

@entity('wars_mission_objective',
        base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
        iconsprite='editor/wars_mission_objective.vmt',
        networked=True)
class WarsMissionObjective(CBaseEntity):
    ''' Defines the Mission Objective entity. 
    
        Each mission objective is displayed as an entry in the hud of the player.
    '''
    # Class variables
    objectivelist = set()

    # States for state field
    STATE_INPROGRESS = 0
    STATE_COMPLETED = 1
    STATE_FAILED = 2

    # Fields
    description = LocalizedStringField(value='', keyname='description', displayname='Description', helpstring='Description displayed in hud', networked=True, clientchangecallback='OnObjectiveChanged')
    priority = IntegerField(value=0, keyname='priority', displayname='Priority', helpstring='Priority used for sorting', networked=True, clientchangecallback='OnObjectiveChanged')
    visible = BooleanField(value=False, keyname='visible', displayname='Visible', helpstring='Determines if the objective is visible', networked=True, clientchangecallback='OnObjectiveChanged')
    state = IntegerField(value=0, networked=True, clientchangecallback='OnObjectiveChanged')
    
    # Outputs
    oncompleted = OutputField(keyname='OnCompleted')
    onfailed = OutputField(keyname='OnFailed')
    
    # Inputs
    @input(inputname='SetVisible', helpstring='Make objective visible', fieldtype=fieldtypes.FIELD_BOOLEAN)
    def InputSetVisible(self, inputdata):
        self.visible = inputdata.value.Bool()
    
    @input(inputname='SetPriority', helpstring='Changes the priority of the objective (ranking displayed to Player)')
    def InputSetPriority(self, inputdata):
        self.priority = inputdata.value.Int()
        
    @input(inputname='SetCompleted', helpstring='Makes the objective completed and fires the completed output')
    def InputSetCompleted(self, inputdata):
        self.SetCompleted()
        
    @input(inputname='SetFailed', helpstring='Makes the objective failed and fires the failed output')
    def InputSetFailed(self, inputdata):
        self.SetFailed()
        
    @input(inputname='SetInProgress', helpstring='Makes the objective in progress (if not already)')
    def InputSetInProgress(self, inputdata):
        self.SetInProgress()
    
    # Class methods
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)
        
    def __init__(self):
        self.objectivelist.add(self)
        
        super().__init__()
    
    def UpdateOnRemove(self):
        self.objectivelist.discard(self)
        
        super().UpdateOnRemove()
        
    @clientonly_assert
    def OnObjectiveChanged(self):
        GetField(self, 'description').Set(self, self.description) # FIXME: Should auto localize when value changes
        objectivespanel.RebuildObjectiveList(self.objectivelist)
        
    def SetCompleted(self):
        ''' Changes the state of the objective to completed.
            Does nothing in case already completed. 
        '''
        if self.state == self.STATE_COMPLETED:
            return
        self.state = self.STATE_COMPLETED
        self.oncompleted.Set('', self, self)
        
    def SetFailed(self):
        ''' Changes the state of the objective to failed.
            Does nothing in case already failed. 
        '''
        if self.state == self.STATE_FAILED:
            return
        self.state = self.STATE_FAILED
        self.onfailed.Set('', self, self)
        
    def SetInProgress(self):
        ''' Changes the state of the objective to in progress.
            Does nothing in case already in progress. 
        '''
        if self.state == self.STATE_INPROGRESS:
            return
        self.state = self.STATE_INPROGRESS
        
    def BuildObjectInfo(self):
        ''' Builds dictionary for HUD. This is passed to javascript for constructing the objective.'''
        return {
            'description' : self.description,
            'priority' : self.priority,
            'state' : self.state,
        }
        
@entity('wars_mission_timer',
        base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
        iconsprite='editor/wars_mission_timer.vmt',
        networked=True)
class WarsMissionTimerObjective(WarsMissionObjective):
    ''' Timer version of wars_mission_objective.
    
        Just like wars_mission_objective, an entry is displayed in the player's hud with a timer in it.
    '''
    
    # New states
    STATE_INPROGRESS_TIMER = 3
    STATE_INPROGRESS_TIMERPAUSED = 4
    
    # Timed out options
    ONTIMEOUTDO_NOTHING = 0
    ONTIMEOUTDO_COMPLETE = 1
    ONTIMEOUTDO_FAIL = 2

    # Key Fields
    timervalue = FloatField(value=0, keyname='Timer')
    
    ontimeoutdo = IntegerField(value=0, 
                               keyname='ontimeoutdo', 
                               displayname='On Timeout Do', 
                               helpstring='Defines behavior on timeout, in addition to firing the timeout event.',
                               choices = [
                                    (ONTIMEOUTDO_NOTHING, 'Nothing'),
                                    (ONTIMEOUTDO_COMPLETE, 'Complete'),
                                    (ONTIMEOUTDO_FAIL, 'Fail'),
                               ]
    )
    timerthreshold = FloatField(value=10, keyname='timerthreshold', displayname='Timer Threshold', helpstring='Threshold time at which OnThresholdRemaining is fired.')
    
    # Outputs
    ontimedout = OutputField(keyname='OnTimedOut')
    onthresholdremaining = OutputField(keyname='OnThresholdRemaining')
    
    # Variables
    timerend = FloatField(value=0, networked=True, clientchangecallback='OnObjectiveChanged')
    firedthreshold = BooleanField(value=False)
    pauzedtimeleft = None
    
    # Starting, pauzing and resetting the timer
    @input(inputname='Start', helpstring='Starts the timer')
    def InputStart(self, inputdata):
        if self.state == self.STATE_INPROGRESS_TIMER:
            return
            
        # If the timer was pauzed, we should use the pauzed left time
        timervalue = self.timervalue
        if self.state == self.STATE_INPROGRESS_TIMERPAUSED:
            assert self.pauzedtimeleft != None, 'Left pauze timer value should not be None.'
            timervalue = self.pauzedtimeleft
            self.pauzedtimeleft = None
            
        # Change to in progress and start timer think
        self.state = self.STATE_INPROGRESS_TIMER
        self.timerend = gpGlobals.curtime + timervalue
        self.SetThink(self.MissionTimerThink, gpGlobals.curtime)
        
    @input(inputname='Pause', helpstring='Pauzes the timer')
    def InputPauze(self, inputdata):
        if self.state == self.STATE_INPROGRESS_TIMERPAUSED:
            return
        if self.state != self.STATE_INPROGRESS_TIMER:
            return # Can only pauze when the state was in progress
        self.state = self.STATE_INPROGRESS_TIMERPAUSED
        self.pauzedtimeleft = self.timerend - gpGlobals.curtime
        
    @input(inputname='Reset', helpstring='Resets the timer')
    def InputReset(self, inputdata):
        if self.state != self.STATE_INPROGRESS_TIMER:
            return
        
        self.timerend = gpGlobals.curtime + self.timervalue
        self.CheckResetFireThreshold()
        
    # Changing the timer duration
    @input(inputname='SetTime', helpstring='Sets timer to a new time', fieldtype=fieldtypes.FIELD_FLOAT)
    def InputSetTime(self, inputdata):
        self.timervalue = inputdata.value.Float()
        if self.state == self.STATE_INPROGRESS_TIMER:
            self.timerend = gpGlobals.curtime + self.timervalue
            self.CheckResetFireThreshold()
            
    @input(inputname='AddTime', helpstring='Adds time to the existing time', fieldtype=fieldtypes.FIELD_FLOAT)
    def InputAddTime(self, inputdata):
        addtime = inputdata.value.Float()
        self.timervalue += addtime
        if self.state == self.STATE_INPROGRESS_TIMER:
            self.timerend += addtime
            self.CheckResetFireThreshold()
            
    @input(inputname='RemoveTime', helpstring='Removes time from the existing time', fieldtype=fieldtypes.FIELD_FLOAT)
    def InputRemoveTime(self, inputdata):
        removetime = inputdata.value.Float()
        self.timervalue -= removetime
        if self.state == self.STATE_INPROGRESS_TIMER:
            self.timerend -= removetime
            self.CheckResetFireThreshold()
        
    def BuildObjectInfo(self):
        ''' Builds dictionary for HUD. This is passed to javascript for constructing the objective.'''
        return {
            'description' : self.description,
            'priority' : self.priority,
            'state' : self.state,
            'timeleft' : max(0, self.timerend - gpGlobals.curtime),
        }
        
    def CheckResetFireThreshold(self):
        ''' Determines if threshold should be fired again. 
        
            This might be the case after adding time.
        '''
        if not self.firedthreshold:
            return
        timeleft = self.timerend - gpGlobals.curtime
        if timeleft > self.timerthreshold:
            self.firedthreshold = False
        
    def MissionTimerThink(self):
        if self.state != self.STATE_INPROGRESS_TIMER:
            return
            
        if not self.firedthreshold:
            timeleft = self.timerend - gpGlobals.curtime
            if timeleft < self.timerthreshold:
                self.onthresholdremaining.Set('', self, self)
                self.firedthreshold = True
            
        if self.timerend < gpGlobals.curtime:
            # Fire event
            self.ontimedout.Set('', self, self)
            if self.ontimeoutdo == self.ONTIMEOUTDO_COMPLETE:
                self.SetCompleted()
            elif self.ontimeoutdo == self.ONTIMEOUTDO_FAIL:
                self.SetFailed()
            else:
                pass # Up to mapper to change the objective state
            
            return
            
        self.SetNextThink(gpGlobals.curtime + 0.25)
    
@entity('wars_win_condition',
        base=['Targetname', 'Parentname', 'Angles', 'EnableDisable'],
        iconsprite='editor/wars_win_condition.vmt',
        networked=True)
class WarsMissionWinCondition(CBaseEntity):
    def UpdateTransmitState(self):
        return self.SetTransmitState(FL_EDICT_ALWAYS)
        
    # Outputs
    onvictory = OutputField(keyname='OnCompleted')
    onlost = OutputField(keyname='OnFailed')
        
    # Inputs
    @input(inputname='PlayerLost', helpstring='Player lost')
    def InputPlayerLost(self, inputdata):
        gamerules.EndGame([], gamerules.gameplayers)
        self.onvictory.Set('', self, self)
        
    @input(inputname='PlayerVictory', helpstring='Player victory')
    def InputPlayerVictory(self, inputdata):
        gamerules.EndGame(gamerules.gameplayers, [])
        self.onlost.Set('', self, self)
        