"""Commander / Captain role assignment for Frontline.

Lobby rule (later UI): first player on a team to pick Commander wins;
anyone else may pick Captain. Shared ownernumber per team.
"""

ROLE_COMMANDER = 'commander'
ROLE_CAPTAIN = 'captain'
ROLE_SPECTATOR = 'spectator'


class FrontlineRoleHelper(object):
    """Tracks per-player Frontline roles and team ownernumbers.

    Fill in: wire to lobby player dict / gameplayers entries.
    Expected gameplayer extras (proposal):
        data['frontline_role'] = ROLE_COMMANDER | ROLE_CAPTAIN
        data['ownernumber']    = shared team owner (same for cmd + captains)
    """

    def __init__(self, gamerules):
        self.gamerules = gamerules
        # steamid / player index -> role
        self.roles = {}
        # team id -> ownernumber
        self.team_owners = {}

    def GetRole(self, player_or_data):
        """Return ROLE_* for a player entity or gameplayers dict entry."""
        # TODO: resolve steamid / slot and return self.roles[...]
        raise NotImplementedError

    def IsCommander(self, player_or_data):
        return self.GetRole(player_or_data) == ROLE_COMMANDER

    def IsCaptain(self, player_or_data):
        return self.GetRole(player_or_data) == ROLE_CAPTAIN

    def TryClaimCommander(self, team, player_or_data):
        """First claim wins. Return True if assigned, False if team already has one."""
        # TODO
        raise NotImplementedError

    def AssignCaptain(self, team, player_or_data):
        """Assign captain role (allowed anytime while slot open)."""
        # TODO
        raise NotImplementedError

    def EnsureSharedOwnerNumbers(self):
        """Force commander + captains on each team onto one ownernumber."""
        # TODO: mutate gameplayers / player.SetOwnerNumber
        raise NotImplementedError

    def GetCommanderForOwner(self, ownernumber):
        """Return commander player/data for this shared owner, or None."""
        # TODO
        raise NotImplementedError

    def IterCaptainsForOwner(self, ownernumber):
        """Yield captain players sharing this ownernumber."""
        # TODO
        raise NotImplementedError
