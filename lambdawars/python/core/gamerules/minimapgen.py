"""Gamerules that load a map to generate its minimap, started from the Workshop publish page of the menu.

The map loads without units, fog of war, start buildings and hud, and the players can't move. The client
captures the minimap from above (menu.workshop.minimapgen) and returns to the menu, where the player
approves or discards it.
"""
import weakref

from srcbase import FL_FROZEN
from gameinterface import ConVarRef
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from core.units.info import unitlist
from .sandbox import Sandbox, SandBoxInfo

sv_fogofwar = ConVarRef('sv_fogofwar')


class MinimapGeneration(Sandbox):
    """Sandbox without anything on top of the map, so only the map ends up on the minimap."""
    spawnstartbuildings = False
    oldfogofwar = 1

    def InitGamerules(self):
        super().InitGamerules()

        if isserver:
            self.oldfogofwar = sv_fogofwar.GetInt()
            sv_fogofwar.SetValue(0)
            # Units placed in the map, and units spawned by the map later on
            self.RemoveUnits()
            RegisterTickMethod(self.RemoveUnits, 0.5)
        else:
            from menu.workshop import minimapgen
            minimapgen.StartCapture()

    def ShutdownGamerules(self):
        super().ShutdownGamerules()

        if isserver:
            if IsTickMethodRegistered(self.RemoveUnits):
                UnregisterTickMethod(self.RemoveUnits)
            sv_fogofwar.SetValue(self.oldfogofwar)
        else:
            from menu.workshop import minimapgen
            minimapgen.StopCapture()

    def RemoveUnits(self):
        for units in list(unitlist.values()):
            for ref in list(units):
                unit = ref() if isinstance(ref, weakref.ref) else ref
                if unit:
                    unit.Remove()

    def SetupPlayer(self, player):
        super().SetupPlayer(player)
        # No RTS controls while the minimap is captured
        player.AddFlag(FL_FROZEN)

    def AllowSandboxCheats(self):
        return False


class MinimapGenerationInfo(SandBoxInfo):
    """Not shown in the game lobby, loaded through the minimapgen game mode (see core.ApplyGameSettings)."""
    name = 'minimapgen'
    hidden = True
    displayname = '#Sandbox_Name'
    description = '#Sandbox_Description'
    cls = MinimapGeneration
    huds = []
    allowplayerjoiningame = True
