from srcbase import EF_NOSHADOW
from vmath import Vector, AngleVectors
from core.abilities.target import AbilityTargetGroup
from core.units.orders import GroupMoveOrder
from gameinterface import engine
from entities import CBaseAnimating, Activity
from .riot_station import AbilityRiotStation

class GroupRiotFormationMove(GroupMoveOrder):
    def ComputePositions(self, positions_out, center_pos, number_of_positions):
        self.ability.ComputePositions(positions_out, center_pos, number_of_positions)

    def ExecuteUnitForPosition(self, unit, target_pos):
        order = unit.MoveOrderInternal(target_pos, angle=self.ability.targetangle, selection=self.units,
                               originalposition=self.position, target=self.target,
                               findhidespot=self.findhidespot, coverspotsearchradius=self.coverspotsearchradius)
        order.force_face_angle = True

        if isserver:
            unit.DoAbility(AbilityRiotStation.name, queueorder=True)

class AbilityRiotFormation(AbilityTargetGroup):
    # Info
    name = "riot_formation"
    image_name = 'vgui/combine/abilities/combine_riot_formation.vmt'
    rechargetime = 1
    displayname = "#AbilityRiotFormation_Name"
    description = "#AbilityRiotFormation_Description"
    hidden = True
    activatesoundscript = '#riotformation'
    requirerotation = True
    targetatgroundonly = True

    preview_temp_soldier_models = None

    def ComputePositions(self, positions_out, center_pos, number_of_positions):
        if not number_of_positions:
            return

        # Get right direction vector for the rotation
        angles = self.targetangle
        right = Vector()
        AngleVectors(angles, None, right, None)

        # Find positions along line
        positions_out.append(center_pos)
        number_of_positions -= 1

        spacing = 40.0
        i = 1
        while number_of_positions > 0:
            positions_out.append(center_pos + (right * spacing * i))
            number_of_positions -= 1
            if not number_of_positions:
                break

            positions_out.append(center_pos - (right * spacing * i))
            number_of_positions -= 1
            i += 1

    if isclient:
        def CreatePreviewSoldiers(self):
            self.preview_temp_soldier_models = []

            model_name = 'models/police_extended.mdl'

            for i in range(0, len(self.units)):
                engine.LoadModel(model_name)
                inst = CBaseAnimating()
                inst.AddEffects(EF_NOSHADOW)

                if inst.InitializeAsClientEntity(model_name, False):
                    inst.SetRenderColor(0, 255, 0)

                    act = Activity(inst.LookupActivity('ACT_IDLE_HOLD_SHIELD'))
                    inst.SetCycle(0.0)
                    inst.ResetSequence(inst.SelectWeightedSequence(act))

                    self.preview_temp_soldier_models.append(inst)

        def DestroyPreviewSoldiers(self):
            if not self.preview_temp_soldier_models:
                return
            for model in self.preview_temp_soldier_models:
                model.Remove()
            self.preview_temp_soldier_models = []

        def ClearVisuals(self):
            super().ClearVisuals()

            self.DestroyPreviewSoldiers()

        def Frame(self):
            super().Frame()

            if self.stopupdating:
                return

            if self.requirerotation and self.rotatepoint:
                if not self.preview_temp_soldier_models:
                    self.CreatePreviewSoldiers()

                positions = []
                self.ComputePositions(positions, self.rotatepoint, len(self.units))

                # Units could be dying in the selection
                while len(self.preview_temp_soldier_models) > len(self.units):
                    self.preview_temp_soldier_models[-1].Remove()
                    del self.preview_temp_soldier_models[-1]

                for model, pos in zip(self.preview_temp_soldier_models, positions):
                    model.SetAbsAngles(self.targetangle)
                    model.SetAbsOrigin(pos)

    # Ability
    def DoAbility(self):
        riotformation_move = GroupRiotFormationMove(self.player, self.targetpos, self.units)
        riotformation_move.ability = self
        riotformation_move.Apply()

        if isserver:
            self.Completed()
