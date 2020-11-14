:mod:`core`: Units
------------------------------------

.. module:: core.units
   :synopsis: Defines all base unit classes.

The :mod:`core.units` module provides access to information about the units
in game, as well as provides all base unit classes.

.. data:: unitlist

   Reference to the global unit list. This is an dictionary containing lists 
   of units. Each key of the dictionary is an ownernumber (*player*) and 
   the value is the list with units.
   
   Example usage::
   
        unit = unitlist[2][0]
   
.. data:: unitlistpertype

    Reference to global unit list additional sorted on unit type.
    
    Example usage::
    
        unit = unitlist[2]['unit_antlion'][0]

.. data:: unitpopulationcount

    Reference to population count per ownernumber (*player*). Do not modify directly, but use the population methods!
    
    
.. automethod:: core.units.GetUnitInfo

.. automethod:: core.units.PrecacheUnit

.. automethod:: core.units.CreateUnitNoSpawn

.. automethod:: core.units.CreateUnit

.. automethod:: core.units.CreateUnitFancy

.. automethod:: core.units.CreateUnitsInArea
    
.. automethod:: core.units.AddPopulation

.. automethod:: core.units.RemovePopulation

.. automethod:: core.units.GetMaxPopulation

.. automethod:: core.units.CreateBehaviorOverrun

-----------------------
UnitInfo
-----------------------
.. autoclass:: core.units.UnitInfo
    :members:
    
-----------------------
UnitBaseShared
-----------------------
.. autoclass:: core.units.UnitBaseShared
    :members:
    
-----------------------
UnitBase
-----------------------
.. autoclass:: core.units.UnitBase
    :members:
    
-----------------------
UnitBaseCombat
-----------------------
.. autoclass:: core.units.UnitBaseCombat
    :members:
    
-----------------------
UnitBaseCombatHuman
-----------------------
.. autoclass:: core.units.UnitBaseCombatHuman
    :members:
    
-----------------------
UnitComponent
-----------------------
.. autoclass:: unit_helper.UnitComponent
    :members:
    :inherited-members:
    
-----------------------
UnitCombatAnimState
-----------------------
.. autoclass:: core.units.UnitCombatAnimState
    :members:
    :inherited-members:
    
    .. data:: movex

        Move x pose parameter (int).
        
    .. data:: movey

        Move y pose parameter (int).
        
    .. data:: flipmovey

        Flip move y pose parameter value when computed (bool).
        
    .. data:: moveyaw

        Move yaw pose parameter (int).
        
    .. data:: bodyyaw

        Body yaw pose parameter (int).
        
    .. data:: bodypitch

        Body pitch pose parameter (int).
        
    .. data:: leanyaw

        Lean yaw pose parameter (int).
        
    .. data:: leanpitch

        Lean pitch pose parameter (int).
        
    .. data:: newjump

        If True, decompose the jump animations into two animations/activies:
        ACT_MP_JUMP_START and ACT_MP_JUMP_FLOAT. Otherwise use one activity: ACT_MP_JUMP (bool).
        
    .. data:: jumping

        True when jumping (bool).
        
    .. data:: jumpstarttime

        Time jump started (float).
        
    .. data:: firstjumpframe

        First jump frame (bool).
        
    .. data:: playingmisc

        True if playing misc layer (bool).
        
    .. data:: misccycle

        Current misc layer cycle (float).
        
    .. data:: miscblendout

        Current misc layer blend out (float).
        
    .. data:: miscblendin

        Current misc layer blend in (float).
        
    .. data:: miscsequence

        Misc layer sequence (int).
        
    .. data:: misconlywhenstill

        Only update if not moving (bool).
        
    .. data:: miscnooverride

        Do not override the misc layer (bool).
        
    .. data:: miscplaybackrate

        Misc layer playbackrate (float).
        
-----------------------
UnitBaseMoveCommand
-----------------------
.. autoclass:: core.units.locomotion.UnitBaseMoveCommand
    :members:
    :inherited-members:
    
    Command values:
    
        .. data:: forwardmove

            Amount we want to move forward (float).
            
        .. data:: sidemove

            Amount we want to move sideward (float).
            
        .. data:: upmove

            Amount we want to move upward (float).

        .. data:: idealviewangles

            Desired view angles (QAngle).
            
        .. data:: interval

            Simulation interval (float).
            
        .. data:: jump

            Try to jump (bool).
        
    Data (copied before moving, applied after):
    
        .. data:: origin;
        
            origin of the unit (Vector).
        
        .. data:: velocity

            velocity of the unit (Vector).
            
        .. data:: viewangles

            viewangles of the unit (QAngle).
        
    Data for reference:
    
        .. data:: totaldistance
        
            Total distance travelled last locomotion update (float).
        
        .. data:: outwishvel
        
            Out wish velocity (float).
        
        .. data:: outstepheight
        
            Out step height (float).
        
        .. data:: blocker
        
            Blocker if we have a collision (entity).
        
        .. data:: blocker_hitpos
        
            Hit position with blocker (Vector).
        
        .. data:: blocker_dir
        
            Direction when being blocked (Vector).
        

    Settings:
    
        .. data:: maxspeed
        
            Max unit speed.
        
        .. data:: yawspeed
        
            Turn speed in degrees.
    
-----------------------
UnitCombatLocomotion
-----------------------
.. autoclass:: core.units.UnitCombatLocomotion
    :members:
    :inherited-members:
    
    .. data:: stepsize
    
        Step size (float).
        
    .. data:: unitsolidmask
    
        Solid mask used when performing traces for collision testing (int).
        
    .. data:: surfacefriction
    
        Surface friction (float).
        
    .. data:: acceleration
    
        Acceleration (float).
        
    .. data:: airacceleration
    
        Air acceleration (float).
        
    .. data:: worldfriction
    
        World friction (float).
        
    .. data:: stopspeed
    
        Stop speed (float).
        
    .. data:: blocker_hitpos
    
        Block hit position (Vector).

-----------------------
UnitBaseAirLocomotion
-----------------------
.. autoclass:: core.units.UnitBaseAirLocomotion
    :members:
    :inherited-members:
    
    .. data:: desiredheight
    
        Desired fly height (float).
        
-----------------------
UnitCombatNavigator
-----------------------
.. autoclass:: core.units.UnitCombatNavigator
    :members:
    :inherited-members:

    .. data:: idealyaw
    
        Ideal yaw the unit tries to face. 
        -1 means it will not try to face this ideal yaw (degrees).
        
    .. data:: facingtarget
    
        Entity target the unit will try to face. 
        Leave None to disable this behavior (entity).
        
    .. data:: facingtargetpos
    
        Position target the unit will try to face. 
        Leave vec3_origin to disable this behavior (Vector).
        
    .. data:: facingfacetarget
    
        Whether the unit is facing the current desired target (bool).
    
    .. data:: path
    
        Current path of the unit (:class:`core.units.UnitBasePath`).
        
    .. data:: idealyawtolerance
    
        Ideal yaw tolerance (degrees).
        
    .. data:: facingcone
    
        Facing cone (float).
        
.. autoclass:: core.units.UnitBasePath
    :members:
    :inherited-members:
    
    .. data:: goaltype
    
        Goal type (int).
        
    .. data:: goalpos
    
        Goal position (Vector).
        
    .. data:: goalinrangepos
    
        Goal in range position (Vector).

    .. data:: waypointtolerance
    
        Waypoint tolerance (float).
        
    .. data:: goaltolerance
    
        Goal tolerance (float).
        
    .. data:: goalflags
    
        Goal flags (int).
        
    .. data:: minrange
    
        Minimum range goal (float).
        
    .. data:: maxrange
    
        Maximum range goal (float).
        
    .. data:: avoidenemies
    
        Wheter the unit should avoid enemies while moving towards the goal. 
        If false the unit will get stuck when running into an enemy.
        This is usually only desired when the unit goal is an enemy (bool).

-----------------------
UnitCombatSense
-----------------------
.. autoclass:: core.units.UnitCombatSense
    :members:
    :inherited-members:

-----------------------
BaseAction
-----------------------
.. autoclass:: core.units.BaseAction
    :members:

-----------------------
BaseBehavior
-----------------------
.. autoclass:: core.units.BaseBehavior
    :members:
    
-----------------------
BehaviorGeneric
-----------------------
.. autoclass:: core.units.BehaviorGeneric
    :members:
    