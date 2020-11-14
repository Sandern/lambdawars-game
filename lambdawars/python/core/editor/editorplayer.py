from srcbase import IN_SPEED
from vmath import QAngle, Vector, AngleVectors
from entities import entity, CHL2WarsPlayer
from gamerules import gamerules
from gameinterface import engine
from editorsystem import EditorSystem
from fields import GetField

if isclient:
    from core.signals import FireSignalRobust, refreshhud

@entity('editor_player', networked=True)
class EditorPlayer(CHL2WarsPlayer):
    def ClientCommand(self, args):
        command = args[0]
        ability = self.GetSingleActiveAbility()
        if command == 'wars_editor_setplacetoolradius':
            ability.placetoolradius = float(args[1])
            return True
        elif command == 'wars_editor_add_pt_asset':
            ability.AddPlaceToolAsset(args[1])
            return True
        elif command == 'wars_editor_remove_pt_asset':
            ability.RemovePlaceToolAsset(args[1])
            return True
        elif command == 'wars_editor_set_pt_density':
            ability.SetPlaceToolDensity(float(args[1]))
            return True
        elif command == 'wars_editor_set_pt_usenavmesh':
            ability.usenavmesh = bool(int(args[1]))
            return True
        elif command == 'wars_editor_set_pt_attr':
            fieldname = args[1]
            value = args.ArgS().split(fieldname)[1] # Remaining arguments minus fieldname
            field = GetField(ability, fieldname)
            field.Set(ability, value)
            return True
        elif command == 'wars_editor_delete_selection':
            EditorSystem().DeleteSelection()
            return True
        elif command == 'wars_editor_copy_selection':
            EditorSystem().CopySelection()
            return True
        elif command == 'wars_editor_paste_selection':
            EditorSystem().PasteSelection()
            return True
            
        return super().ClientCommand(args)
 
    def OnLeftMouseButtonReleased(self, data):
        super().OnLeftMouseButtonReleased(data)

        if gamerules.activemode == 'select':
            if (self.buttons & IN_SPEED) == 0:
                EditorSystem().ClearSelection()
            EditorSystem().DoSelect(self)
        