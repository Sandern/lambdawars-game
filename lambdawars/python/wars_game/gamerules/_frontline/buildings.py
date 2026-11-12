"""Captain building interact / operate / bunker rules."""

# Buildings captains may operate (production menus). Scrapyard IS operable.
# Passive-only / no-queue stay on the deny list.
DEFAULT_OPERABLE_HINTS = (
    # TODO: fill with build_* names or flags
    # 'build_reb_barracks', 'build_reb_junkyard', 'build_comb_garrison', ...
)

DEFAULT_DENY_OPERATE = (
    # Pure passive eco / housing / props
    # 'build_comb_powergenerator', 'build_reb_billet', barricades, ...
)


class FrontlineBuildingInteract(object):
    def __init__(self, gamerules):
        self.gamerules = gamerules
        # building handle -> captain player currently operating
        self.operators = {}

    def CanOperate(self, building):
        """False for passive-only; True for scrapyard / barracks / etc."""
        # TODO
        raise NotImplementedError

    def TryOperate(self, player, building):
        """Exclusive operator; locked RTS cam; show building abilities."""
        # TODO
        raise NotImplementedError

    def ExitOperate(self, player):
        # TODO
        raise NotImplementedError

    def OnUseHq(self, player, hq):
        """Upgrade / role popup only — do not garrison HQ."""
        # TODO
        raise NotImplementedError

    def OnUseBunker(self, player, bunker):
        """Combat garrison; locked RTS; multiple captains allowed; no pop cost."""
        # TODO
        raise NotImplementedError

    def CaptainIgnoresPopulation(self, unit):
        """Army pop + bunker maxpopulation ignore for captain bodies."""
        return True

    def CommanderMayEjectAnyone(self):
        """Including captains — use stock garrison unload."""
        return True
