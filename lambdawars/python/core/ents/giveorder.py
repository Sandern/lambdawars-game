""" A convenient entity for ordering groups of units.
"""
from entities import entity, CPointEntity, entlist, MouseTraceData
from fields import StringField, FloatField, TargetSrcField, TargetDestField, BooleanField, FlagsField, OutputField, input, fieldtypes

@entity('wars_give_order',
        iconsprite='editor/wars_give_order.vmt')
class GiveOrder(CPointEntity):
    def __init__(self):
        super().__init__()
        
        self.units = []
        self.unitsqueue = set()
        self.atleastoneunitsuccess = False
        
    def MonitorInterceptThink(self):
        """ Monitors unit sensing for option SF_GIVEORDER_INTERCEPTCANCEL.
            Cancels the order of the unit if an enemy is encountered. """
        if not self.units:
            return
        for unit in list(self.units):
            enemy = unit.senses.GetNearestEnemy()
            minrange = self.interceptcancelminrange if self.interceptcancelminrange > 0 else unit.maxattackrange
            if not enemy or (unit.GetAbsOrigin() - enemy.GetAbsOrigin()).Length2D() > minrange:
                continue
            self.CancelOrder([unit])
                
        self.SetNextThink(gpGlobals.curtime + 0.1, 'MonitorIntercept')
        
    def OnUnitOrderFinished(self, unit):
        try:
            self.units.remove(unit)
        except ValueError:
            PrintWarning('wars_give_order: Unit not in list\n')
            return
            
        if unit.IsAlive():
            self.atleastoneunitsuccess = True
            self.onorderperformed.Set(unit, unit, self)
        
        # If no units are left we are finished
        if not self.units:
            if self.atleastoneunitsuccess:
                self.onorderperformedall.Set('', self, self)
            else:
                self.onorderinterrupted.Set('', self, self)
                
    def DelayedPerformOrderThink(self):
        target = None
        if self.targetordername:
            target = entlist.FindEntityByName(None, self.targetordername)
            if not target:
                PrintWarning('wars_give_order.DelayedPerformOrderThink: could not find order target %s\n' % (self.targetordername))
 
        if target:
            targetpos = target.GetAbsOrigin()
        else:
            targetpos = self.GetAbsOrigin()
    
        for unit in self.unitsqueue:
            # For now skip units which are already ordered
            if not unit or unit in self.units:
                continue
                
            # Clear existing orders if specified
            if self.overwriteexistingorders:
                for o in unit.orders:
                    if o.callback == self.OnUnitOrderFinished:
                        o.callback = None
                unit.ClearAllOrders(False, dispatchevent=False)
                
            # Execute the type of order
            if self.abilityname:
                # Assumes target type ability
                leftpressed = MouseTraceData()
                leftpressed.endpos = targetpos
                leftpressed.groundendpos = targetpos
                leftpressed.ent = target
                mouse_inputs=[('leftpressed', leftpressed)]
                abi = unit.DoAbility(self.abilityname, mouse_inputs=mouse_inputs)
                order = None
                for o in unit.orders:
                    if o.ability == abi:
                        order = o
                        break
                        
                if order:
                    order.callback = self.OnUnitOrderFinished
                    self.units.append(unit)
                else:
                    PrintWarning('wars_give_order PerformOrder: could not find unit order for ability after performing %s\n' % (self.abilityname))
            else:
                # Default to move order
                o = unit.MoveOrder(targetpos, self.GetAbsAngles(), target=target)
                o.callback = self.OnUnitOrderFinished
                self.units.append(unit)
            
        self.unitsqueue = set()
        
        # Enable Monitor Intercept think
        if self.HasSpawnFlags(self.SF_GIVEORDER_INTERCEPTCANCEL):
            self.SetThink(self.MonitorInterceptThink, gpGlobals.curtime + 0.1, 'MonitorIntercept')
                
    def PerformOrder(self, units):
        ''' Performs the order on the input units.
            Extends the existing list of units performing the order.
        '''
        self.unitsqueue |= set(units)
        self.SetThink(self.DelayedPerformOrderThink, gpGlobals.curtime)
        
    def CancelOrder(self, units):
        for unit in list(units):
            o = None
            for idx, o in enumerate(unit.orders):
                if o.callback == self.OnUnitOrderFinished:
                    break
                    
            if not o:
                continue
                
            # Clear callback so it won't call OnUnitOrderFinished
            o.callback = None
            unit.ClearOrder(idx)
            self.units.remove(unit)
    
        # Fire the order interrupted output if not units are left
        if not self.units:
            self.onorderinterrupted.Set('', self, self)
        
    @input(inputname='PerformOrder', helpstring='Perform the setup order. It performs the order on all the units with the defined name in keyvalue "Unit name<String>".')
    def InputPerformOrder(self, inputdata):
        self.atleastoneunitsuccess = False
        
        # Collect units
        units = []
        unit = entlist.FindEntityByName(None, self.unittargetname)
        while unit:
            units.append(unit)
            unit = entlist.FindEntityByName(unit, self.unittargetname)
            
        # Perform order on the selected units
        if not units:
            PrintWarning('InputPerformOrder: could not find units with name %s\n' % (self.unittargetname))
            return
            
        self.PerformOrder(units)
        
    @input(inputname='PerformOrderUnit', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Perform the order on the input unit. It ignores the keyvalue "Unit name<String>" and performs the order on the input unit only.')
    def InputPerformOrderUnit(self, inputdata):
        unit = inputdata.value.Entity()
        self.PerformOrder([unit])
        
    @input(inputname='CancelOrder', helpstring='Stops all units performing the order')
    def InputCancelOrder(self, inputdata):
        self.CancelOrder(self.units)
        
    unittargetname = TargetSrcField(keyname='unitname', displayname='Unit Target Name', helpstring='Target name of units on which this should be performed')
    overwriteexistingorders = BooleanField(value=True, keyname='overwriteexistingorders', displayname='Overwrite Existing Orders', helpstring='Overwrite existing orders that are performed on the unit right now by other wars_give_order entities.')
    abilityname = StringField(value='', keyname='abilityname', displayname='Ability', helpstring='Optional target type ability to be executed by the unit')
    targetordername = TargetDestField(keyname='targetordername', displayname='Order Target', helpstring='Optional target entity for order')
    interceptcancelminrange = FloatField(value=0, keyname='interceptcancelminrange', displayname='Intercept Cancel Min Range', helpstring='Minimal range for intercept cancel')
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_GIVEORDER_INTERCEPTCANCEL', ( 1 << 0 ), False, 'Intercept Cancel'),
        ],
        cppimplemented=True)
    
    onorderperformed = OutputField(keyname='OnOrderPerformed', displayname='OrderPerformed', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when a unit performed the order. Outputs the unit as argument.')
    onorderperformedall = OutputField(keyname='OnOrderPerformedall', displayname='OrderPerformedAll', helpstring='Fired when a ALL units performed the order. It also fires the output when some units die on the way.')
    onorderinterrupted = OutputField(keyname='OnOrderInterrupted', displayname='OrderInterrupted', helpstring='Outputs when the order has been interrupted. By Input CancelOrder, Keyvalue "Intercept cancel" or when all units are dead.')
