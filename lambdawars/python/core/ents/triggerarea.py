from srcbase import FSOLID_NOT_SOLID, FSOLID_TRIGGER
from entities import CBaseEntity, SOLID_BBOX
from fields import BooleanField

# Entity similar to CBaseTrigger
class CTriggerArea(CBaseEntity):
    """Simple trigger volume that tracks entities touching its bounds.

    Can be enabled/disabled at runtime and keeps a set of entity handles
    currently inside the volume for game logic to query.
    """
    def __init__(self):
        super().__init__()
        
        self.touchingents = set()
        
    def Spawn(self):
        """Initialize trigger bounds, solid flags, and enabled state."""
        self.SetSolid(SOLID_BBOX)
        self.AddSolidFlags(FSOLID_NOT_SOLID)

        super().Spawn()
        
        if self.startdisabled:
            self.Disable()
        else:
            self.Enable()
        
    def Enable(self):
        """Enable trigger collisions so StartTouch/EndTouch are fired."""
        self._disabled = False
        
        if self.VPhysicsGetObject():
            self.VPhysicsGetObject().EnableCollisions( True )

        if not self.IsSolidFlagSet(FSOLID_TRIGGER):
            self.AddSolidFlags(FSOLID_TRIGGER)
            self.PhysicsTouchTriggers()
    
    def Disable(self):
        """Disable the trigger and clear the list of touching entities."""
        self._disabled = True
        self.touchingents = set()
        
        if self.VPhysicsGetObject():
            self.VPhysicsGetObject().EnableCollisions(False)

        if self.IsSolidFlagSet(FSOLID_TRIGGER):
            self.RemoveSolidFlags(FSOLID_TRIGGER)
            self.PhysicsTouchTriggers()
    
    def StartTouch(self, ent):
        """Record that an entity has started touching the trigger volume."""
        if not self._disabled:
            self.touchingents.add(ent.GetHandle())
    
    def EndTouch(self, ent):
        """Record that an entity has stopped touching the trigger volume."""
        self.touchingents.discard(ent.GetHandle())
            
    _disabled = False
    startdisabled = BooleanField(value=False, keyname='StartDisabled')