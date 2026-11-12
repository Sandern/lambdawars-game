"""HQ FIFO respawn queue for starter captain bodies.

- unit_cpt_engineer / unit_cpt_stalker
- costs = [] (free)
- wait = unit buildtime
- FIFO by death time; same timestamp -> random.shuffle / random.choice
- While waiting: locked RTS camera (FrontlineCameraPolicy)
- On complete: SetControlledUnit
"""

import random


class FrontlineRespawnQueue(object):
    def __init__(self, gamerules):
        self.gamerules = gamerules
        # list of dicts: {player, faction, death_time, state, unit_handle, ...}
        self.queue = []

    def OnCaptainDeath(self, player, unit):
        """Enqueue starter replacement for this captain."""
        # TODO: append entry; start HQ produce if idle
        raise NotImplementedError

    def GetStarterUnitName(self, faction_name):
        """Return 'unit_cpt_engineer' or 'unit_cpt_stalker'."""
        # TODO
        raise NotImplementedError

    def SortQueue(self):
        """Order by death_time; break ties with random."""
        # TODO: stable sort + random among equal death_time
        raise NotImplementedError

    def Think(self):
        """Advance builds / auto-possess when ready. Call from gamerules MainThink."""
        # TODO
        raise NotImplementedError

    def CancelForPlayer(self, player):
        # TODO
        raise NotImplementedError
