from core.resources import ResourceInfo
from entities import entitylist

# Resources..
class ResRequisitionInfo(ResourceInfo):
    name = 'requisition'
    iconname = 'vgui/icons/icon_requisition'
    displayname = '#ResRequisition_Name'
    
class ResKillsInfo(ResourceInfo):
    name = 'kills'
    iconname = 'vgui/icons/icon_requisition'
    displayname = '#ResRequisition_Name'
    
class ResGrubsInfo(ResourceInfo):
    name = 'grubs'
    
    @classmethod
    def TakeResources(cls, ownernumber, amount):  
        n = amount
        grub = entitylist.FindEntityByClassname(None, "unit_antliongrub")
        while grub and n > 0:
            if not grub.IsMarkedForDeletion() and grub.IsResource() and grub.GetOwnerNumber() == ownernumber:
                grub.Remove()
                n -= 1
            grub = entitylist.FindEntityByClassname(grub, "unit_antliongrub")

    @classmethod
    def GiveResources(cls, ownernumber, amount): 
        # Find an antlion colony, then add grubs
        colony = entitylist.FindEntityByClassname(None, "build_ant_colony")
        if not colony:
            PrintWarning('GrubGiveResources: No antlion colony found to give grubs to\n')
            return
        colony.AddGrubs(amount)
    
class ResPowerInfo(ResourceInfo):
    name = 'power'
    iconname = 'vgui/icons/icon_energy'
    iscapped = True
    nocapoverflow = True
    displayname = '#ResPower_Name'
    
class ResScrapInfo(ResourceInfo):
    name = 'scrap'
    iconname = 'vgui/icons/icon_scrap'
    displayname = '#ResScrap_Name'

# Resource for Squad Wars
class ResPowerCharInfo(ResourceInfo):
    name = 'power_sw'
    iconname = 'vgui/icons/icon_energy'
    iscapped = True
    nocapoverflow = True
    displayname = '#ResPower_Name'

    