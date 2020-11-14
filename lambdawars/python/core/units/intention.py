""" """
import srcmgr
srcmgr.VerifyIsServer()
from unit_helper import UnitComponent
from gameinterface import ConVar, ConVarRef, FCVAR_CHEAT
from entities import ACT_INVALID
import traceback

developer = ConVarRef('developer')
unit_intention = ConVar('unit_intention', '-1', FCVAR_CHEAT)

# Transition types
CONTINUE = ''  # NOTE: This is an empty string, so that it evaluates to False when testing.
CHANGETO = 'CHANGETO'
SUSPENDFOR = 'SUSPENDFOR'
DONE = 'DONE'


class BaseAction(object):
    def __init__(self, outer, behavior):
        super().__init__()
        
        self.outer = outer
        self.behavior = behavior
        
    def Init(self):
        """ Initializes the action. """
        pass
        
    # Action Transitions
    # Return these in the action processing
    def Continue(self):
        """ No transition, continue this Action next think. """
        return CONTINUE
        
    def ChangeTo(self, nextaction, reason, *args, **kwargs):
        """ Exit the current Action and transition into NextAction.

            Args:
                nextaction (BaseAction): action class to which to change
                reason (str): string describing the reason, for debug purposes.
        """
        if not self.valid:
            DevMsg(1, '#%s INVALID CHANGETO, already in transition: next action is %s for reason "%s"\n\tDiscarding action %s with reason "%s"\n' % 
                      (self.outer.entindex(), str(self.nextaction), self.reason, nextaction, reason))
            return CONTINUE
        self.nextaction = nextaction(self.outer, self.behavior)
        self.nextaction.Init(*args, **kwargs)
        self.reason = reason
        return CHANGETO
        
    def SuspendFor(self, nextaction, reason, *args, **kwargs):
        """ Put the current Action 'on hold' (bury it) and enter NextAction

            Args:
                nextaction (BaseAction): action class for which to suspend
                reason (str): string describing the reason, for debug purposes.
        """
        if not self.valid:
            DevMsg(1, '#%s INVALID SUSPENDFOR, already in transition: next action is %s for reason "%s"\n\tDiscarding action %s with reason "%s"\n' % 
                      (self.outer.entindex(), str(self.nextaction), self.reason, nextaction, reason))
            return CONTINUE
        self.nextaction = nextaction(self.outer, self.behavior)
        self.nextaction.Init(*args, **kwargs)
        self.reason = reason
        return SUSPENDFOR
        
    def Done(self, reason):
        """ This Action is finished. Resume the 'buried' Action.

            Args:
                reason (str): string describing the reason, for debug purposes.
        """
        if not self.valid:
            DevMsg(1, '#%s INVALID DONE, already in transition: next action is %s for reason "%s"\n\tDiscarding DONE with reason "%s"\n' % 
                      (self.outer.entindex(), str(self.nextaction), self.reason, reason))
            return CONTINUE
        self.reason = reason
        return DONE

    # Encapsulation of Action processing
    def OnStart(self):
        """ Executed when the Action is transtioned into 
            Can return an immediate transition """
        pass
            
    def Update(self):
        """ Does the 'work' of the Action
            Update can return a transition to a new Action """
        return self.Continue()
            
    def OnEnd(self):
        """ Is executed when the Action is transitioned out of """
        pass
        
    def OnSuspend(self):
        """ Executed when Action has been put on hold for another Action
            Can return a transition """
        return None
        
    def OnResume(self):
        """ Executed when Action resumes after being suspended
            Can return a transition (perhaps Action is no longer valid) """
        return None

    # Helpers
    def SuspendForWaitForMainActivity(self, reason='Wait for main activity'):
        return self.SuspendFor(self.behavior.ActionWaitForActivity, reason,
                               self.outer.animstate.specificmainactivity)

    # Debug
    def GetDebugString(self):
        """  Optional for debugging. Returns a string that is displayed
            for the top action when using the command unit_show_actions_debug.
        """
        return ''
        
    @property
    def is_active_action(self):
        """ Returns True in case this action is currently the active action. """
        try:
            return self.behavior.actions[-1] == self
        except IndexError:
            return False

    #: An action is no longer valid after being ended.
    valid = True
    #: Next action to be executed after calling ChangeTo or SuspendFor
    nextaction = None
    #: Debug reason string for transition to other state
    reason = '<not set>'


class BaseBehavior(UnitComponent):
    """ The base behavior class for units. This class manages the actions. """
    crashed = False
    last_ai_crash = 0.0

    in_on_start_call = False

    def __init__(self, outer):
        super().__init__(outer)
        
        # Set the default starting action to ActionIdle
        self.StartingAction = self.ActionIdle
        
        # Stack with actions. The top action is the active actions.
        # The other actions are "buried".
        self.actions = []
        
    def Destroy(self):
        """ Destroy/clean up the behavior class. """
        self.EndTopActions(0)
     
    # Transition handling
    def EndTopActions(self, fromidx):
        """ Ends actions from given index to top.

            Args:
                fromidx (int): Index from which to start
        """
        actions_to_end = self.actions[fromidx:]
        self.actions = self.actions[0:fromidx] # Remove actions in case OnEnd dispatches an event
        for action in reversed(actions_to_end):
            action.OnEnd()
            action.valid = False

    def HandleContinue(self, action):
        """ Handles the continue case.

            Args:
                action (BaseAction): Action wishing to continue

            Returns:
                bool: True on success
        """
        self.in_on_start_call = False
        return True
        
    def HandleChangeTo(self, action):
        """ Changes to a new action, ending the current one.

            Args:
                action (BaseAction): Action which wants to change.

            Returns:
                bool: True on success
        """
        self.in_on_start_call = False

        if developer.GetInt() >= 2:
            if unit_intention.GetInt() == -1 or unit_intention.GetInt() == self.outer.entindex():
                DevMsg(2, '#%s %s (%f) -> %s changed to %s (%s)\n' % (
                    self.outer.entindex(), self.__class__.__name__, gpGlobals.curtime, action.__class__.__name__,
                    action.nextaction.__class__.__name__, action.reason))
                    
        # End this action and any actions that are on top of this action
        idx = self.actions.index(action)
        self.EndTopActions(idx)
            
        # Change to the new action
        new_action = action.nextaction
        self.actions.append(new_action)

        self.in_on_start_call = True
        new_transition = new_action.OnStart()
        self.handlers[new_transition](self, new_action)
        
        return True
        
    def HandleSuspendFor(self, action):
        """ Suspends current action for a new action.

            Args:
                action (BaseAction): Action which wants to suspend.

            Returns:
                bool: True on success
        """
        self.in_on_start_call = False

        if developer.GetInt() >= 2:
            if unit_intention.GetInt() == -1 or unit_intention.GetInt() == self.outer.entindex():
                DevMsg(2, '#%s %s (%f) -> %s suspended for %s (%s)\n' % (
                    self.outer.entindex(), self.__class__.__name__, gpGlobals.curtime, action.__class__.__name__,
                    action.nextaction.__class__.__name__, action.reason))

        is_suspended = not (action == self.actions[-1])
 
        # End any actions that are on top of this action
        idx = self.actions.index(action)  
        self.EndTopActions(idx+1)

        # NOTE: Might already be suspended
        if not is_suspended:
            # Tell action it is suspended
            suspend_transition = self.actions[-1].OnSuspend()
            self.handlers[suspend_transition](self, self.actions[-1])
        
        # Suspend for the new action
        new_action = action.nextaction
        self.actions.append(new_action)

        self.in_on_start_call = True
        new_transition = new_action.OnStart()
        self.handlers[new_transition](self, new_action)
        
        return True
            
    def HandleDone(self, action):
        """ Ends the action, resuming the buried action.

            Args:
                action (BaseAction): Action that is done.

            Returns:
                bool: True on success
        """
        if developer.GetInt() >= 2:
            if unit_intention.GetInt() == -1 or unit_intention.GetInt() == self.outer.entindex():
                DevMsg(2, '#%s %s (%f) -> %s is done (%s)\n' % (
                    self.outer.entindex(), self.__class__.__name__, gpGlobals.curtime,
                    action.__class__.__name__, action.reason))
    
        # End this action and any actions that are on top of this action
        idx = self.actions.index(action)
        self.EndTopActions(idx)

        if self.in_on_start_call:
            self.in_on_start_call = False

            new_action = self.ActionNoop(self.outer, self)
            new_action.Init()
            self.actions.append(new_action)
            new_action.OnStart()
        else:
            # Resume buried one
            try:
                resume_transition = self.actions[-1].OnResume()
                self.handlers[resume_transition](self, self.actions[-1])
            except IndexError:
                PrintWarning('#%d: %s transitioned into Done while no actions are on the stack!\n' % (
                    self.outer.entindex(), action.__class__.__name__))
                self.InitDefaultAction()

        return True   
            
    handlers = {
        None: HandleContinue,
        CONTINUE: HandleContinue,
        CHANGETO: HandleChangeTo,
        SUSPENDFOR: HandleSuspendFor,
        DONE: HandleDone,
    } 
            
    def DispatchEvent(self, eventname, *args):
        """ Dispatches to the event to each action until an action handles it.

            Returning None will let the event be handled by the next handler.
            Returning any other transition will eat the event and perform the transition.
            Return Continue to not have a transition, eat the event and do something in the active
            Action itself.

            Args:
                eventname (str): Event being dispatched
                *args: arguments of event
        """
        # Start with the innermost child action
        # If no response try buried actions.
        for action in reversed(self.actions):
            if not action.valid:
                continue
            handler = getattr(action, eventname, None)
            if not handler:
                continue
            transition = handler(*args)
            if transition is not None:
                if developer.GetInt() >= 2:
                    if unit_intention.GetInt() == -1 or unit_intention.GetInt() == self.outer.entindex():
                        DevMsg(2, '#%s %s %s (%f) -> Action %s responded to event %s with %s\n' % (
                            self.outer.entindex(), self.outer.__class__.__name__, self.__class__.__name__, gpGlobals.curtime,
                            action.__class__.__name__, eventname, transition or 'Continue'))
                self.handlers[transition](self, action)
                return True
                
    def InitDefaultAction(self):
        action = self.StartingAction(self.outer, self)
        action.Init()
        self.actions.append(action)
        self.in_on_start_call = True
        transition = action.OnStart()
        if self.handlers[transition](self, action):
            return False
        return True
        
    #
    # Run routine
    #
    def Run(self):
        """ Maintains the current action. Handles transitions."""
        try:
            if not self.actions:
                if not self.InitDefaultAction():
                    return

            action = self.actions[-1]
            transition = action.Update()
            self.handlers[transition](self, action)
        except Exception:
            outer = self.outer
            if gpGlobals.curtime - self.last_ai_crash < outer.think_freq * 2:
                self.Run = self.RunCrashed
                self.crashed = True
                PrintWarning('#%d Unit AI Crashed (%s). Disabling.\n' % (outer.entindex(),
                                                                         outer.GetClassname()))
                return
            PrintWarning('#%d Unit AI Crashed (%s). Restarting.\n' % (outer.entindex(), outer.GetClassname()))
            if outer.orders:
                PrintWarning('\tOrders during crash:\n\t- %s\n' % '\n\t- '.join(map(str, outer.orders)))
            traceback.print_exc()  
            self.actions = []
            self.last_ai_crash = gpGlobals.curtime
            
    def RunCrashed(self):
        pass

    #
    # Debug
    #    
    def ActionsToString(self):
        actions = ''
        for i, a in enumerate(self.actions):
            if i != 0:
                actions += '( '
            actions += a.__class__.__name__
        actions += ' )' * (len(self.actions)-1)
        return actions
        
    def DrawActions(self, debugtextoffset, showactiondebug=False):
        text = '%s: %s %s' % (self.__class__.__name__, self.ActionsToString(), '(crashed)' if self.crashed else '')
        if showactiondebug and self.actions:
            text += ' - %s' % (self.actions[-1].GetDebugString())
        self.outer.EntityText(debugtextoffset, text, 0.1)

    # Action list shared by all behaviors
    class ActionIdle(BaseAction):
        """ Idle action."""
        pass

    class ActionNoop(BaseAction):
        """ Action that delays resuming to the next action by one unit think interval.
            This 'may' be needed when an action returns Done from an OnStart, which is
            kind of unusual. Since the unit might get stuck in a recursive loop in this
            case, we delay resuming to the next think cycle this way.
        """
        def Update(self):
            return self.Done('One think cycle delay unit AI')

    class ActionInterruptible(object):
        """ Action containing interruptable events. """
        def OnKilled(self):
            return self.ChangeTo(self.behavior.ActionDie, 'Changing to die action')

        def OnStunned(self):
            return self.ChangeTo(self.behavior.ActionStunned, 'Changing to stunned action')

        def OnChangeToAction(self, action):
            return self.ChangeTo(action, 'Changing to action %s' % action)

    class ActionWaitForActivity(BaseAction):
        """ Waits until the activity is finished.
        
            Returns the transition Done when done.
        """
        def Init(self, activity=None):
            """ Action initialize method.
            
                Arguments:
                activity - the activty the action should wait for.
            """
            super().Init()

            self.activity = activity

        def OnStart(self):
            self.oldaimoving = self.outer.aimoving
            self.outer.aimoving = True
            if not self.activity:
                self.activity = self.SetupActivity()
            if self.activity == ACT_INVALID:
                return self.OnStartInvalidActivity()
                
        def OnEnd(self):
            super().OnEnd()

            self.outer.aimoving = self.oldaimoving

        def SetupActivity(self):
            """ Called when no activity was provided as argument. """
            return self.outer.animstate.specificmainactivity

        def OnStartInvalidActivity(self):
            """ Called when not a valid activity on start. So it can be overridden. """
            return self.Done('Invalid activity')

        def OnSpecificActivityEnded(self, specificactivity):
            if specificactivity != self.activity:
                return
            return self.EndSpecificActivity()

        def OnSpecificActivityInterrupted(self, specificactivity):
            """ This could happen if some logic overrides the active specific activity while it's playing.

                Likely a logic bug, but we end the action anyway.
            """
            if specificactivity != self.activity:
                return
            return self.EndSpecificActivity()

        def EndSpecificActivity(self):
            """ For actions that inherit from this action, can hook into the Done transition
                is returned. Useful for dispatching events, as that should not be done from OnEnd. """
            return self.Done('Activity done')
            
    class ActionWaitForActivityTransition(BaseAction):
        """ To be used in case you want to change to a new action, 
            but you first want to wait for an animation to finish."""
        def Init(self, activity, transitionaction, *args, **kwargs):
            """ Initialize method.
            
                Args:
                   activity (Activity): the activity the action should wait for.
                   transitionaction (action): the action the unit should change to after
                                   playing the activity.
                   args: arguments passed to transitionaction.
                   kwargs: keyword arguments passed to transitionaction.
            """
            self.activity = activity
            self.transitionaction = transitionaction
            self.args = args
            self.kwargs = kwargs
            
        def OnStart(self):
            self.oldaimoving = self.outer.aimoving
            self.outer.aimoving = True
            if not self.activity:
                self.activity = self.outer.animstate.specificmainactivity
            if self.activity == ACT_INVALID:
                return self.ChangeTo(self.transitionaction, 'Invalid activity, changing to transition', *self.args, **self.kwargs)
        
        def OnEnd(self):
            self.outer.aimoving = self.oldaimoving
            
        def OnSpecificActivityEnded(self, specificactivity):
            if specificactivity == self.activity:
                return self.ChangeTo(self.transitionaction, 'Activity done, changing to transition', *self.args, **self.kwargs)
    
    # Versions of the above with auto movement.
    class ActionWaitForActivityAutoMovement(ActionWaitForActivity):
        """ Same as ActionWaitForActivity, but auto moves using
            the predefined animation movement."""
        def OnStart(self):
            self.outer.locomotionenabled = False
            return super().OnStart()

        def Update(self):
            self.outer.AutoMovement()
            return super().Update()

        def OnEnd(self):
            self.outer.locomotionenabled = True
            return super().OnEnd()
            
    class ActionWaitForActivityTransitionAutoMovement(ActionWaitForActivityTransition):
        """ Same as ActionWaitForActivityTransition, but auto moves using
            the predefined animation movement."""
        def OnStart(self):
            self.outer.locomotionenabled = False
            return super().OnStart()

        def Update(self):
            self.outer.AutoMovement()
            return super().Update()

        def OnEnd(self):
            self.outer.locomotionenabled = True
            return super().OnEnd()
            
    class ActionAbility(BaseAction):
        """ Base action for abilities."""
        def Init(self, order):
            """ Inialize method.
            
                Args:
                   order (Order): Instance of the ability order.
            """
            super().Init()
            self.order = order

        def OnResume(self):
            if self.outer.curorder != self.order:
                return self.ChangeToIdle('Received new order')
            return super().OnResume()
            
        def OnNewOrder(self, order):
            return self.ChangeToIdle('Received new order')
        
        def OnAllOrdersCleared(self):
            return self.ChangeToIdle('Order cleared')
            
        def ChangeToIdle(self, reason):
            if not self.changetoidleonlostorder:
                return None
            autocasted = self.order.ability.autocasted
            return self.ChangeTo(self.behavior.ActionIdle, reason, updateidleposition=not autocasted)
            
        changetoidleonlostorder = True
            
    class ActionAbilityWaitForActivity(ActionInterruptible, BaseAction):
        """ Waits until the activity is finished."""
        def Init(self, order):
            """ Initialize method.
            
                Args:
                   order (Order): Instance of the ability order.
            """
            super().Init()
            self.order = order
            
        def OnStart(self):
            self.oldaimoving = self.outer.aimoving
            self.outer.aimoving = True
            self.activity = self.outer.animstate.specificmainactivity
            if self.activity == ACT_INVALID:
                self.order.Remove(dispatchevent=False)
                return self.ChangeTo(self.behavior.ActionIdle, 'Invalid activity, order cleared')
                
        def OnEnd(self):
            outer = self.outer

            outer.aimoving = self.oldaimoving

            if outer.curorder == self.order:
                self.order.Remove(dispatchevent=False)
        
        def OnSpecificActivityEnded(self, specificactivity):
            if specificactivity == self.activity:
                return self.ChangeTo(self.behavior.ActionIdle, 'Activity done, order cleared')
                
    class ActionWait(BaseAction):
        """ Waits for given time. """
        def Init(self, waittime):
            super().Init()
            self.waittime = waittime

        def OnStart(self):
            self.waitendtime = gpGlobals.curtime + self.waittime
            self.OnWaitStart()
            return self.Continue()
            
        def Update(self):
            if self.waitendtime < gpGlobals.curtime:
                trans = self.OnWaitFinished()
                if trans:
                    return trans
                return self.Done('Done waiting')
            return self.Continue()
            
        def OnWaitStart(self):
            pass
            
        def OnWaitFinished(self):
            return None
