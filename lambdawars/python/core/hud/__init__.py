from core.usermessages import usermessage

if isclient:
    from srcbase import Color
    from . info import HudInfo
    from . abilities import BaseHudAbilities
    from . buildings import HudBuildSingleUnit, HudBuildConstruction
    from . infobox import BaseHudInfo, AbilityHudInfo, UnitHudInfo, QueueUnitHudInfo
    from . minimap import BaseHudMinimap, minimapflash
    from . units import HudUnitsContainer, BaseHudUnits, BaseHudSingleUnit, BaseHudSingleUnitCombat, BaseHudGarrisonUnits
    from . resourceindicator import HudResourceIndicator, hudresourceindicator
    from . notifier import HudNotifier, NotifierLine, hudnotifier
    from . groups import BaseHudGroups
    from . abilitybutton import AbilityButton
    
    from . player_names import HudPlayerNames
    from . import cunit_display # TODO: Make optional?
    
    from vgui import localize
    
    # Used by notifications system to insert messages
    def DoInsertMessage(notification, text, icon=None, color=Color(255, 255, 0, 255)):
        if text and text[0] == '#':
            localizedtext = localize.Find(text)
                
        hudnotifier.Get().InsertMessage(
            NotifierLine(notification, text, icon=icon, color=color)
        )


# User messages
@usermessage('_rind')
def InsertResourceIndicator(origin, *args, **kwargs):
    n = len(args)
    hudresourceindicator.Get().Add(origin, args[0] if n > 0 else '1', args[1] if n > 1 else None)
