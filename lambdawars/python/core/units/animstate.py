"""Animation state classes for Lambda Wars units.

Provides animation state management and event handlers for unit animations.
"""
from srcbase import *
from vmath import *

from entities import Activity
from unit_helper import UnitBaseAnimState, UnitAnimState, UnitAnimStateEx

def clamp(val, min, max):
    """Clamp a value between min and max.
    
    Args:
        val: Value to clamp.
        min: Minimum value.
        max: Maximum value.
        
    Returns:
        Clamped value.
    """
    if val > max:
        return max
    elif val < min:
        return min
    return val

class EventHandlerAnimation(object):
    """Event handler for animation activities."""
    def __init__(self, activity):
        """Initialize animation event handler.
        
        Args:
            activity: Activity to play.
        """
        self.activity = activity
        
    def Setup(self, cls):
        """Setup handler by resolving activity reference.
        
        Args:
            cls: Class to resolve activity from.
            
        Returns:
            EventHandlerAnimation: New handler with resolved activity.
        """
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
        """Return a new handler instance with the resolved activity.
        
        Args:
            activity: Resolved activity.
            
        Returns:
            EventHandlerAnimation: New handler instance.
        """
        return self.__class__(activity)
        
    def __call__(self, unit, data):
        """Handle animation event.
        
        Args:
            unit: Unit entity.
            data: Event data (playback rate if non-zero).
        """
        animstate = unit.animstate
        animstate.specificmainactivity = animstate.TranslateActivity(Activity(self.activity))
        if data != 0: 
            animstate.specmainactplaybackrate = float(data) / 255.0
        animstate.RestartMainSequence()

class EventHandlerAnimationMisc(EventHandlerAnimation):
    """Event handler for misc animation sequences."""
    def __init__(self, activity, onlywhenstill=True, miscplaybackrate=1.0):
        """Initialize misc animation handler.
        
        Args:
            activity: Activity to play.
            onlywhenstill (bool): Only play when unit is still.
            miscplaybackrate (float): Default playback rate.
        """
        super().__init__(activity)
        
        self.onlywhenstill = onlywhenstill
        self.miscplaybackrate = miscplaybackrate
        
    def ReturnNewHandler(self, activity):
        """Return new handler with same settings.
        
        Args:
            activity: Resolved activity.
            
        Returns:
            EventHandlerAnimationMisc: New handler instance.
        """
        return self.__class__(activity, onlywhenstill=self.onlywhenstill, miscplaybackrate=self.miscplaybackrate)
        
    def __call__(self, unit, data):
        """Handle misc animation event.
        
        Args:
            unit: Unit entity.
            data: Event data (playback rate if non-zero).
        """
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
    """Event handler for custom animation activities."""
    def __call__(self, unit, data):
        """Handle custom animation event.
        
        Args:
            unit: Unit entity.
            data: Activity ID.
        """
        animstate = unit.animstate
        animstate.specificmainactivity = animstate.TranslateActivity(Activity(data))
        animstate.RestartMainSequence()

class EventHandlerGesture(object):
    """Event handler for gesture animations."""
    def __call__(self, unit, data):
        """Handle gesture event.
        
        Args:
            unit: Unit entity.
            data: Activity ID for gesture.
        """
        animstate = unit.animstate
        animstate.miscsequence = animstate.SelectWeightedSequence(animstate.TranslateActivity(Activity(data)))
        animstate.playermisc = True
        animstate.misccycle = 0
        animstate.misconlywhenstill = False
        animstate.miscnooverride = True
        animstate.miscplaybackrate = 1.0

class EventHandlerJump(object):
    """Event handler for jump animations."""
    def __call__(self, unit, data):
        """Handle jump event.
        
        Args:
            unit: Unit entity.
            data: Unused.
        """
        animstate = unit.animstate
        animstate.jumping = True
        animstate.firstjumpframe = True
        animstate.jumpstarttime = gpGlobals.curtime
        animstate.RestartMainSequence() 

class EventHandlerEndSpecAct(object):
    """Event handler for ending specific activities."""
    def __call__(self, unit, data):
        """Handle end specific activity event.
        
        Args:
            unit: Unit entity.
            data: Unused.
        """
        unit.animstate.EndSpecificActivity()

class EventHandlerSound(object):
    """Event handler for playing sounds."""
    def __init__(self, soundscriptname):
        """Initialize sound event handler.
        
        Args:
            soundscriptname (str): Name of sound script to play.
        """
        super().__init__()
        
        self.soundscriptname = soundscriptname

    def __call__(self, unit, data):
        """Handle sound event.
        
        Args:
            unit: Unit entity.
            data: Unused.
        """
        unit.EmitSound(self.soundscriptname)

class EventHandlerMulti(object):
    """Wraps multiple event handlers to one event."""
    def __init__(self, *args):
        """Initialize multi event handler.
        
        Args:
            *args: Event handlers to wrap.
        """
        super().__init__()
        self.events = list(args)
        
    def Setup(self, cls):
        """Setup all wrapped handlers.
        
        Args:
            cls: Class to resolve handlers from.
        """
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
        """Call all wrapped handlers.
        
        Args:
            unit: Unit entity.
            data: Event data.
        """
        for eh in self.eventhandlers:
            eh(unit, data)

class UnitCombatAnimState(UnitAnimState):
    """Animation state for combat units."""
    def OnNewModel(self):
        """Setup pose parameters and other model related stuff."""
        studiohdr = self.outer.GetModelPtr()
        self.moveyaw = self.outer.LookupPoseParameter(studiohdr, "move_yaw")
        
    def OnEndSpecificActivity(self, specificactivity):
        """Handle end of specific activity.
        
        Args:
            specificactivity: Activity that ended.
            
        Returns:
            Activity: Next activity to play, or construct activity if constructing.
        """
        # Keep playing construct activity as long as we are constructing
        outer = self.outer
        if outer.constructing:
            return outer.constructactivity
            
        # Dispatch event for unit ai
        outer.DispatchEvent('OnSpecificActivityEnded', specificactivity)
        return super().OnEndSpecificActivity(specificactivity)

    def OnInterruptSpecificActivity(self, specificactivity):
        """Handle interruption of specific activity.
        
        Called when the passed specificactivity was interrupted.
        In this case OnEndSpecificActivity will never be called.
        
        Args:
            specificactivity: Activity that was interrupted.
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
