"""Captain camera policy.

Alive on foot  -> FPS via SetControlledUnit
Operate/bunker/respawn wait -> RTS view, camera LOCKED (no free strategic pan)
Captains never get free strategic camera for the match.
"""


class FrontlineCameraPolicy(object):
    def __init__(self, gamerules):
        self.gamerules = gamerules

    def ApplyCaptainFps(self, player, unit):
        """Possess unit; ensure FPS config / move type."""
        # TODO: player.SetControlledUnit(unit)
        raise NotImplementedError

    def ApplyLockedRts(self, player, focus_entity=None):
        """Leave FPS; show locked RTS/building context camera."""
        # TODO: SetControlledUnit(None); block pan/zoom; optional focus
        raise NotImplementedError

    def OnEnterOperateBuilding(self, player, building):
        # TODO
        raise NotImplementedError

    def OnEnterBunker(self, player, bunker):
        # TODO
        raise NotImplementedError

    def OnRespawnWaiting(self, player):
        # TODO
        raise NotImplementedError

    def OnExitLocked(self, player, unit=None):
        """Restore FPS on unit if provided."""
        # TODO
        raise NotImplementedError

    def BlockStrategicInput(self, player):
        """Hook/usercmd filter so captains cannot free-cam."""
        # TODO
        raise NotImplementedError
