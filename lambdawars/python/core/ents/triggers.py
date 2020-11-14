from entities import entity, CBaseTrigger
if isserver:
    from entities import FL_EDICT_ALWAYS
    
@entity('trigger_nobuildings', networked=True)
class TriggerNoBuildings(CBaseTrigger):
    if isclient:
        def __init__(self):
            super().__init__()
        
            self.SetOverrideClassname('trigger_nobuildings')
    else:
        def UpdateTransmitState(self):
            return self.SetTransmitState(FL_EDICT_ALWAYS)

        def Spawn(self):
            super().Spawn()

            # So the trigger is detectable on the client
            self.clientsidepredicted = True
            
            self.InitTrigger()
            self.Enable()