"""Captain body switch at HQ.

unit_cpt_*     -> morph (SetUnitType / AbilityTransformUnit style), wait buildtime
regular army   -> replace entity at normal production building, wait buildtime
"""


class FrontlineBodySwitch(object):
    def __init__(self, gamerules):
        self.gamerules = gamerules

    def IsCaptainUnitType(self, unitinfo_name):
        """True if name starts with unit_cpt_ (morph path)."""
        return bool(unitinfo_name) and unitinfo_name.startswith('unit_cpt_')

    def BeginSwitch(self, player, target_unitinfo_name):
        """Start morph or replace after unlock check. Non-blocking channel."""
        # TODO
        raise NotImplementedError

    def MorphCaptainUnit(self, unit, target_unitinfo_name, transform_time):
        """Same entity: channel transform_time then SetUnitType + weapons."""
        # TODO: mirror core.units.abilities.unittransform.AbilityTransformUnit
        raise NotImplementedError

    def ReplaceWithRegularUnit(self, player, old_unit, target_unitinfo_name):
        """Despawn old; queue/spawn at normal prod building; possess when ready."""
        # TODO
        raise NotImplementedError

    def GetProductionBuildingForUnit(self, ownernumber, unitinfo_name):
        """Find alive building that normally produces this unit (e.g. Special Ops)."""
        # TODO
        raise NotImplementedError
