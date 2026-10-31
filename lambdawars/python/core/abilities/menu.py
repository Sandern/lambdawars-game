"""Menu system for organizing abilities into sub-menus.

Provides classes for creating hierarchical ability menus that can be
navigated in the HUD. Allows grouping related abilities together and
providing navigation between menu levels.
"""
from .base import AbilityBase, SendAbilityMenuChanged

def CreateSubMenu(namesrc, displaynamesrc, descriptionsrc, image_namesrc, abilitiessrc):
    """Create a new sub-menu ability class dynamically.
    
    Args:
        namesrc (str): Internal name for the menu.
        displaynamesrc (str): Display name shown in HUD.
        descriptionsrc (str): Description text for the menu.
        image_namesrc (str): Icon image path.
        abilitiessrc (dict): Dictionary of abilities to include in the menu.
    """
    class AbilityMenu(AbilityMenuBase):
        name = namesrc
        displayname = displaynamesrc
        description = descriptionsrc
        image_name = image_namesrc
        abilities = abilitiessrc

class SubMenu(str):
    """String subclass representing a sub-menu in the ability hierarchy.
    
    When instantiated, creates a new menu ability that contains other
    abilities. Used for organizing abilities into groups.
    """
    def __new__(cls, name, displayname, description, image_name='vgui/abilities/ability_unknown.vmt', abilities=None):
        obj = str.__new__(cls, name)
        if not abilities:
            abilities = {}
        obj.abilities = abilities
        
        # Define new menu ability
        CreateSubMenu(name, displayname, description, image_name, abilities)
            
        return obj

class AbilityMenuBase(AbilityBase):
    """Base class for menu abilities that organize other abilities into sub-menus.
    
    Menu abilities are hidden from normal ability lists and instead create
    sub-menus in the HUD that contain other abilities. Used for organizing
    abilities into logical groups.
    """
    name = 'menu'
    hidden = True
    clientonly = True
    
    def Init(self):
        super().Init()
        
        try:
            self.player.hudabilitiesmap.append(self.abilities)
        except AttributeError:
            self.player.hudabilitiesmap = [self.abilities]

        SendAbilityMenuChanged()
        
    def ClientUpdateAbilitiesMenu(self):
        """Update the abilities menu on the client.
        
        Called when the menu structure changes. Override to add custom
        client-side menu update logic.
        """
        pass
                
class AbilityMenuUp(AbilityBase):
    """Ability for navigating up one level in the ability menu hierarchy.
    
    Provides a way to exit sub-menus and return to the parent menu level.
    """
    name = 'menuup'
    displayname = '#MenuUp_Name'
    description = '#MenuUp_Description'
    image_name = 'vgui/abilities/cancel.vmt'
    hidden = True
    clientonly = True
    abilities = {}
    
    def Init(self):
        super().Init()
        
        try:
            self.player.hudabilitiesmap.pop()
        except AttributeError:
            pass
            
        SendAbilityMenuChanged()
    