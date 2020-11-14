''' AN entity which allows you to output an input unit randomly.
'''
import random
from entities import entity, CPointEntity, entlist, MouseTraceData
from fields import StringField, FloatField, TargetSrcField, TargetDestField, BooleanField, FlagsField, OutputField, input, fieldtypes

@entity('wars_choose_random_order',
        iconsprite='editor/wars_choose_random_order.vmt')
class GiveOrderRandom(CPointEntity):
    @input(inputname='InputTriggerUnit', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Takes the input unit and outputs it randomly, from one if the outputs.')
    def InputTriggerUnit(self, inputdata):
        unit = inputdata.value.Entity()
        totalvalue = (self.onTriggerOutput01Chance+self.onTriggerOutput02Chance+self.onTriggerOutput03Chance+self.onTriggerOutput04Chance+self.onTriggerOutput05Chance+self.onTriggerOutput06Chance+self.onTriggerOutput07Chance+self.onTriggerOutput08Chance)
        randomevalue = random.random()* totalvalue
        betweenvalue = self.onTriggerOutput01Chance
        
        if self.onTriggerOutput01Chance > 0 and randomevalue <= betweenvalue:
            self.onTriggerOutput01.Set(unit, unit, self)
        
        if self.onTriggerOutput02Chance > 0 and randomevalue > betweenvalue and randomevalue <= (betweenvalue+self.onTriggerOutput02Chance):
            self.onTriggerOutput02.Set(unit, unit, self)
        
        betweenvalue += self.onTriggerOutput02Chance
        if self.onTriggerOutput03Chance > 0 and randomevalue > (betweenvalue) and randomevalue <= (betweenvalue+self.onTriggerOutput03Chance):
            self.onTriggerOutput03.Set(unit, unit, self)
        
        betweenvalue += self.onTriggerOutput03Chance
        if self.onTriggerOutput04Chance > 0 and randomevalue > (betweenvalue) and randomevalue <= (betweenvalue+self.onTriggerOutput04Chance):
            self.onTriggerOutput04.Set(unit, unit, self)
            
        betweenvalue += self.onTriggerOutput04Chance
        if self.onTriggerOutput05Chance > 0 and randomevalue > (betweenvalue) and randomevalue <= (betweenvalue+self.onTriggerOutput05Chance):
            self.onTriggerOutput05.Set(unit, unit, self)
            
        betweenvalue += self.onTriggerOutput05Chance
        if self.onTriggerOutput06Chance > 0 and randomevalue > (betweenvalue) and randomevalue <= (betweenvalue+self.onTriggerOutput06Chance):
            self.onTriggerOutput06.Set(unit, unit, self)

        betweenvalue += self.onTriggerOutput06Chance
        if self.onTriggerOutput07Chance > 0 and randomevalue > (betweenvalue) and randomevalue <= (betweenvalue+self.onTriggerOutput07Chance):
            self.onTriggerOutput07.Set(unit, unit, self)
            
        betweenvalue += self.onTriggerOutput07Chance
        if self.onTriggerOutput08Chance > 0 and randomevalue > (betweenvalue) and randomevalue <= (betweenvalue+self.onTriggerOutput08Chance):
            self.onTriggerOutput07.Set(unit, unit, self)
            
    onTriggerOutput01Chance = FloatField(value=1.0, keyname='ontriggeroutput01chance', displayname='Trigger Output 01 Chance', helpstring='Chance that the unit will be outputted form Output01. (From 0 to 1)')
    onTriggerOutput02Chance = FloatField(value=1.0, keyname='ontriggeroutput02chance', displayname='Trigger Output 02 Chance', helpstring='Chance that the unit will be outputted form Output02. (From 0 to 1)')
    onTriggerOutput03Chance = FloatField(value=1.0, keyname='ontriggeroutput03chance', displayname='Trigger Output 03 Chance', helpstring='Chance that the unit will be outputted form Output03. (From 0 to 1)')
    onTriggerOutput04Chance = FloatField(value=1.0, keyname='ontriggeroutput04chance', displayname='Trigger Output 04 Chance', helpstring='Chance that the unit will be outputted form Output04. (From 0 to 1)')
    onTriggerOutput05Chance = FloatField(value=1.0, keyname='ontriggeroutput05chance', displayname='Trigger Output 05 Chance', helpstring='Chance that the unit will be outputted form Output05. (From 0 to 1)')
    onTriggerOutput06Chance = FloatField(value=1.0, keyname='ontriggeroutput06chance', displayname='Trigger Output 06 Chance', helpstring='Chance that the unit will be outputted form Output06. (From 0 to 1)')
    onTriggerOutput07Chance = FloatField(value=1.0, keyname='ontriggeroutput07chance', displayname='Trigger Output 07 Chance', helpstring='Chance that the unit will be outputted form Output07. (From 0 to 1)')
    onTriggerOutput08Chance = FloatField(value=1.0, keyname='ontriggeroutput08chance', displayname='Trigger Output 08 Chance', helpstring='Chance that the unit will be outputted form Output08. (From 0 to 1)') 
    
    onTriggerOutput01 = OutputField(keyname='TriggerOutput01', displayname='OnTriggerOutput01', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput02 = OutputField(keyname='TriggerOutput02', displayname='OnTriggerOutput02', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput03 = OutputField(keyname='TriggerOutput03', displayname='OnTriggerOutput03', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput04 = OutputField(keyname='TriggerOutput04', displayname='OnTriggerOutput04', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput05 = OutputField(keyname='TriggerOutput05', displayname='OnTriggerOutput05', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput06 = OutputField(keyname='TriggerOutput06', displayname='OnTriggerOutput06', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput07 = OutputField(keyname='TriggerOutput07', displayname='OnTriggerOutput07', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    onTriggerOutput08 = OutputField(keyname='TriggerOutput08', displayname='OnTriggerOutput08', fieldtype=fieldtypes.FIELD_EHANDLE, helpstring='Fired when randomly chosen. Outputs the unit as argument.')
    

