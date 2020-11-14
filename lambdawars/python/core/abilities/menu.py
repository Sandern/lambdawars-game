from .base import AbilityBase, SendAbilityMenuChanged

def CreateSubMenu(namesrc, displaynamesrc, descriptionsrc, image_namesrc, abilitiessrc):
    class AbilityMenu(AbilityMenuBase):
        name = namesrc
        displayname = displaynamesrc
        description = descriptionsrc
        image_name = image_namesrc
        abilities = abilitiessrc

class SubMenu(str):
    def __new__(cls, name, displayname, description, image_name='vgui/abilities/ability_unknown.vmt', abilities=None):
        obj = str.__new__(cls, name)
        if not abilities:
            abilities = {}
        obj.abilities = abilities
        
        # Define new menu ability
        CreateSubMenu(name, displayname, description, image_name, abilities)
            
        return obj

class AbilityMenuBase(AbilityBase):
    """ """
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
        pass
                
class AbilityMenuUp(AbilityBase):
    """ """
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
    