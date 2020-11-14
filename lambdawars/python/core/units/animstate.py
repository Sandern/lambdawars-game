from srcbase import *
from vmath import *

from entities import Activity
from unit_helper import UnitBaseAnimState, UnitAnimState, UnitAnimStateEx

def clamp(val, min, max):
    if val > max:
        return max
    elif val < min:
        return min
    return val

class EventHandlerAnimation(object):
    def __init__(self, activity):
        self.activity = activity
        
    def Setup(self, cls):
        if type(self.activity) != str:
            return
        # Keep expanding until we found the activity.
        # In some cases it first refers to an attribute containing the string name
        # of the activity.
        activity = self.activity
        while type(activity) == str:
            activity = getattr(cls, activity)
        # Return new handler
        return self.ReturnNewHandler(activity)
        
    def ReturnNewHandler(self, activity):
        return self.__class__(activity)
        
    def __call__(self, unit, data):
        animstate = unit.animstate
        animstate.specificmainactivity = animstate.TranslateActivity(Activity(self.activity))
        if data != 0: 
            animstate.specmainactplaybackrate = float(data) / 255.0
        animstate.RestartMainSequence()

class EventHandlerAnimationMisc(EventHandlerAnimation):
    def __init__(self, activity, onlywhenstill=True, miscplaybackrate=1.0):
        super().__init__(activity)
        
        self.onlywhenstill = onlywhenstill
        self.miscplaybackrate = miscplaybackrate
        
    def ReturnNewHandler(self, activity):
        return self.__class__(activity, onlywhenstill=self.onlywhenstill, miscplaybackrate=self.miscplaybackrate)
        
    def __call__(self, unit, data):
        animstate = unit.animstate
        animstate.miscsequence = animstate.SelectWeightedSequence(animstate.TranslateActivity(Activity(self.activity)))
        animstate.playermisc = True
        animstate.misccycle = 0
        animstate.misconlywhenstill = self.onlywhenstill
        animstate.miscnooverride = True
        if data != 0: 
            animstate.miscplaybackrate = float(data) / 255.0
        else:
            animstate.miscplaybackrate = self.miscplaybackrate

class EventHandlerAnimationCustom(object):
    def __call__(self, unit, data):
        animstate = unit.animstate
        animstate.specificmainactivity = animstate.TranslateActivity(Activity(data))
        animstate.RestartMainSequence()

class EventHandlerGesture(object):
    def __call__(self, unit, data):
        animstate = unit.animstate
        animstate.miscsequence = animstate.SelectWeightedSequence(animstate.TranslateActivity(Activity(data)))
        animstate.playermisc = True
        animstate.misccycle = 0
        animstate.misconlywhenstill = False
        animstate.miscnooverride = True
        animstate.miscplaybackrate = 1.0

class EventHandlerJump(object):
    def __call__(self, unit, data):
        animstate = unit.animstate
        animstate.jumping = True
        animstate.firstjumpframe = True
        animstate.jumpstarttime = gpGlobals.curtime
        animstate.RestartMainSequence() 

class EventHandlerEndSpecAct(object):
    def __call__(self, unit, data):
        unit.animstate.EndSpecificActivity()

class EventHandlerSound(object):
    def __init__(self, soundscriptname):
        super().__init__()
        
        self.soundscriptname = soundscriptname

    def __call__(self, unit, data):
        unit.EmitSound(self.soundscriptname)

class EventHandlerMulti(object):
    """ Wraps multiple event handlers to one event. """
    def __init__(self, *args):
        super().__init__()
        self.events = list(args)
        
    def Setup(self, cls):
        self.eventhandlers = []
        for i in range(0, len(self.events)):
            handler = self.events[i]
            if type(handler) == str:
                handler = getattr(cls, handler)
            if hasattr(handler, 'Setup'):
                newhandler = handler.Setup(cls)
                if newhandler:
                    handler = newhandler
            self.eventhandlers.append(handler)
        
    def __call__(self, unit, data):
        for eh in self.eventhandlers:
            eh(unit, data)

class UnitCombatAnimState(UnitAnimState):
    def OnNewModel(self):
        """ Setup pose parameters and other model related stuff """
        studiohdr = self.outer.GetModelPtr()
        self.moveyaw = self.outer.LookupPoseParameter(studiohdr, "move_yaw")
        
    def OnEndSpecificActivity(self, specificactivity):
        # Keep playing construct activity as long as we are constructing
        outer = self.outer
        if outer.constructing:
            return outer.constructactivity
            
        # Dispatch event for unit ai
        outer.DispatchEvent('OnSpecificActivityEnded', specificactivity)
        return super().OnEndSpecificActivity(specificactivity)

    def OnInterruptSpecificActivity(self, specificactivity):
        """ Called when the passed specificactivity was interrupted.
            In this case OnEndSpecificActivity will never be called.
        """
        # Dispatch event for unit ai
        self.outer.DispatchEvent('OnSpecificActivityInterrupted', specificactivity)
        super().OnInterruptSpecificActivity(specificactivity)

class UnitCombatAnimStateEx(UnitAnimStateEx):
    def OnNewModel(self):
        """ Setup pose parameters and other model related stuff """
        studiohdr = self.outer.GetModelPtr()
        self.moveyaw = self.outer.LookupPoseParameter(studiohdr, "move_yaw")
        
    def OnEndSpecificActivity(self, specificactivity):
        # Keep playing construct activity as long as we are constructing
        outer = self.outer
        if outer.constructing:
            return outer.constructactivity
            
        # Dispatch event for unit ai
        outer.DispatchEvent('OnSpecificActivityEnded', specificactivity)
        return super().OnEndSpecificActivity(specificactivity)
