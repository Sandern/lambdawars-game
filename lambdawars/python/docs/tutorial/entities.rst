.. _tut-entities:

**********************************
Entities
**********************************
Entities are the monsters, doors, switches and lights that turn your static 
architecture into an interactive environment (see 
`VDC <http://developer.valvesoftware.com/wiki/Entity_Creation>`_).
Python entities are supported on both server and client in a natural way with basic networking support.

A simple entity
============================
The following example is an entity used in the Overrun gamemode for spawning
enemies, extended with several methods and comments::

    from entities import CPointEntity, entity
    from fields import input, BooleanField
    
    @entity('overrun_wave_spawnpoint')
    class OverrunWaveSpawnPoint(CPointEntity):
        # This method is called when the entity is spawned into the world
        # Initialize your entity here
        def Spawn(self):
            super(OverrunWaveSpawnPoint, self).Spawn()
            
        # This method is called when the entity is removed from the world
        # All your cleaning up should be done here.
        def UpdateOnRemove(self):
            super(OverrunWaveSpawnPoint, self).UpdateOnRemove()
            
        # Enable/Disable method which can be triggered from Hammer
        @input(inputname='Enable')
        def InputEnable(self, inputdata):
            self.disabled = False
            
        @input(inputname='Disable')
        def InputDisable(self, inputdata):
            self.disabled = True
            
        disabled = BooleanField(value=False, keyname='StartDisabled')

This entity uses :class:`entities.CPointEntity` as base class, which is a pointed-size server 
only class. Furthermore it places the **entity** decorator in front of the
class definition (see `decorators <http://docs.python.org/glossary.html#term-decorator>`_). 
This decorator will link our Python class to a Map class name. The first argument is used
for this name.

The input decorator can be used to link a method to an input from Hammer. Additional most
of the fields support the keyname argument, which you can use to link variables to Hammer
(like the disabled variable).

Networking
============================
You can network an entity in Python by simply adding the additional argument ``networked=True``
to the entity decorator::

    from entities import entity
    from core.units import UnitBase
    from fields import BooleanField

    @entity('unit_networked_test', networked=True)
    class NetworkedUnit(UnitBase):
        if isserver:
            # Only define Spawn on the server
            def Spawn(self):
                super(NetworkedUnit, self).Spawn()
                
                # Change our networked boolean to True on server Spawn of this entity
                # This will transmit the value to all clients
                self.somebool = True
                
        somebool = BooleanField(value=False, networked=True)
        
This entity class will be created on both the server and client.
Common methods like Spawn and UpdateOnRemove will be called on
both sides. However, the entity will not be created on the client
until the transmission rules permit it. For example, an unit hidden
in the fog of war will not be transmitted to the player (and is
not created yet).

