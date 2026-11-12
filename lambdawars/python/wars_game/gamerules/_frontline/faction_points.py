"""Personal faction points (Lambda / Overwatch) for Frontline.

Team requisition/power/scrap stay on resources[ownernumber].
Personal FP must NOT use that shared dict alone — store per player.
"""

# Resource type names (also stubbed in wars_game.resources)
FP_REBELS = 'lambda'
FP_COMBINE = 'overwatch'

# Test costs (scale later)
DEFAULT_KIT_UNLOCK_FP = 10
DEFAULT_COMMANDER_ABILITY_FP = 10


class FrontlineFactionPoints(object):
    """Per-player FP balances and spend helpers."""

    def __init__(self, gamerules):
        self.gamerules = gamerules
        # key: steamid or player index -> int
        self.balances = {}

    def GetFpTypeForFaction(self, faction_name):
        """Return 'lambda' or 'overwatch' from faction id string."""
        # TODO: map destroyhq_rebels / rebels -> lambda, combine -> overwatch
        raise NotImplementedError

    def GetBalance(self, player_or_steamid):
        # TODO
        raise NotImplementedError

    def Give(self, player_or_steamid, amount=1):
        """Award whole FP (milestones always grant exactly 1 unless amount passed)."""
        # TODO
        raise NotImplementedError

    def CanAfford(self, player_or_steamid, cost):
        # TODO
        raise NotImplementedError

    def Spend(self, player_or_steamid, cost):
        """Return True if spent. Never go negative."""
        # TODO
        raise NotImplementedError

    def TryUnlockKit(self, player, kit_unitinfo_name, cost=DEFAULT_KIT_UNLOCK_FP):
        """Permanent-for-match kit unlock. Return True on success."""
        # TODO: check already unlocked; Spend; record unlock set
        raise NotImplementedError

    def HasUnlockedKit(self, player, kit_unitinfo_name):
        # TODO
        raise NotImplementedError

    def TryBuyCommanderAbility(self, player, ability_name, cost=DEFAULT_COMMANDER_ABILITY_FP):
        """Spend FP for commander faction ability (still needs techrequirements)."""
        # TODO
        raise NotImplementedError
