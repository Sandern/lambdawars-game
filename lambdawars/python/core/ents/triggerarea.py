from srcbase import FSOLID_NOT_SOLID, FSOLID_TRIGGER
from entities import CBaseEntity, SOLID_BBOX
from fields import BooleanField

# Entity similar to CBaseTrigger
class CTriggerArea(CBaseEntity):
    def __init__(self):
        super().__init__()
        
        self.touchingents = set()
        
    def Spawn(self):
        self.SetSolid(SOLID_BBOX)
        self.AddSolidFlags(FSOLID_NOT_SOLID)

        super().Spawn()
        
        if self.startdisabled:
            self.Disable()
        else:
            self.Enable()
        
    def Enable(self):
        self._disabled = False
        
        if self.VPhysicsGetObject():
            self.VPhysicsGetObject().EnableCollisions( True )

        if not self.IsSolidFlagSet(FSOLID_TRIGGER):
            self.AddSolidFlags(FSOLID_TRIGGER)
            self.PhysicsTouchTriggers()
    
    def Disable(self):
        self._disabled = True
        self.touchingents = set()
        
        if self.VPhysicsGetObject():
            self.VPhysicsGetObject().EnableCollisions(False)

        if self.IsSolidFlagSet(FSOLID_TRIGGER):
            self.RemoveSolidFlags(FSOLID_TRIGGER)
            self.PhysicsTouchTriggers()
    
    def StartTouch(self, ent):
        if not self._disabled:
            self.touchingents.add(ent.GetHandle())
    
    def EndTouch(self, ent):
        self.touchingents.discard(ent.GetHandle())
            
    _disabled = False
    startdisabled = BooleanField(value=False, keyname='StartDisabled')