"""Milestone counters -> 1 FP at thresholds.

Captain personal awards:
  - 1 FP per 5 kills by their character
  - 1 FP per 100 requisition spent (production / unlocks)
  - 1 FP per 100 requisition worth of buildings they constructed
  - 1 FP per control point they contributed to capturing

Commander/owner credit uses shared ownernumber (no spillover %).
"""

KILLS_PER_FP = 5
REQ_SPEND_PER_FP = 100
REQ_CONSTRUCT_PER_FP = 100


class FrontlineMilestones(object):
    def __init__(self, gamerules, faction_points):
        self.gamerules = gamerules
        self.fp = faction_points
        # steamid -> counters dict
        self.counters = {}

    def _Counter(self, key):
        if key not in self.counters:
            self.counters[key] = {
                'kills': 0,
                'req_spend': 0,
                'req_construct': 0,
            }
        return self.counters[key]

    def OnCaptainKill(self, captain_player, victim):
        """Call when captain-controlled unit gets a kill."""
        # TODO: increment kills; every KILLS_PER_FP -> fp.Give(..., 1)
        raise NotImplementedError

    def OnCaptainReqSpent(self, captain_player, amount, category='production'):
        """category: 'production' | 'unlock' | etc."""
        # TODO: accumulate req_spend; every REQ_SPEND_PER_FP -> 1 FP
        raise NotImplementedError

    def OnCaptainConstructProgress(self, captain_player, requisition_value):
        """Add completed building req value toward construct milestone."""
        # TODO
        raise NotImplementedError

    def OnCaptainCaptureContribute(self, captain_player, control_point):
        """1 FP per point contributed."""
        # TODO: fp.Give(captain_player, 1)
        raise NotImplementedError

    def HookSignals(self):
        """Connect to game signals (kills, resources spent, CP capture)."""
        # TODO: core.signals receivers
        raise NotImplementedError

    def UnhookSignals(self):
        # TODO
        raise NotImplementedError
