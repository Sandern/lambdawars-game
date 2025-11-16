""" Base for throwable objects.

Could be anything. Derives from base grenade. Provides some useful methods for setup.
The default behavior will be to explode on touch, but override Detonate to change it.
"""
from entities import CBaseGrenade as BaseClass
from fields import FloatField

class ThrowableObject(BaseClass):
    spawntime = FloatField(value=0)

    def Spawn(self):
        """Store spawn time for the throwable object and call the base spawn."""
        self.spawntime = gpGlobals.curtime
        
        super().Spawn()

    def SetVelocity(self, velocity, angVelocity):
        """Apply linear and angular velocity to the underlying physics object."""
        physobj = self.VPhysicsGetObject()
        if physobj is not None:
            physobj.AddVelocity(velocity, angVelocity)
