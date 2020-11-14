from core.units import CoverSpot
from wars_game.abilities.steadyposition import AbilitySteadyPosition


class AbilityRiotStation(AbilitySteadyPosition):
    name = 'riot_station'
    displayname = "#AbilityRiotStation_Name"
    description = "#AbilityRiotStation_Description"
    image_name = 'vgui/combine/abilities/combine_hold_ground.vmt'
    steadytime = 1.0
    recharge_other_abilities = ['riot_formation']
    sai_hint = set(['']) # Bots don't use cover points at all anyway

    if isserver:
        class ActionInSteadyPosition(AbilitySteadyPosition.ActionInSteadyPosition):
            def OnStart(self):
                outer = self.outer

                transition = super().OnStart()

                outer.OnSteadyPositionChanged()

                outer.cover_spot_override = CoverSpot(type=2, angle=outer.GetAbsAngles().y)
                outer.in_cover = 2
                outer.OnInCoverChanged()  # TODO: Add support for properties in fields (incover)

                return transition

            def OnEnd(self):
                super().OnEnd()

                outer = self.outer

                outer.OnSteadyPositionChanged()

                outer.cover_spot_override = None
                outer.in_cover = 0
                outer.OnInCoverChanged()  # TODO: Add support for properties in fields (incover)

        class ActionDoSteadyPosition(AbilitySteadyPosition.ActionDoSteadyPosition):
            def OnStart(self):
                outer = self.outer
                outer.steadying = True

                self.channel_animation = outer.ANIM_SHIELD_STATIONED_SETUP

                return super().OnStart()

            def OnEnd(self):
                super().OnEnd()

                outer = self.outer
                outer.steadying = False

