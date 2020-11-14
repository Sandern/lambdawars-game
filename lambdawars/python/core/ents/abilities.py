from entities import CPointEntity, entity
from fields import OutputField, fieldtypes, input, GetField
from core.abilities import GetAbilityInfo, GetTechNode
from core.signals import abilitycanceled, abilitycompleted
from core.attributemgr import AbilityInfoSetAttr, ApplyAbilityAttribute

@entity('wars_ability_manager',
        base=['Targetname', 'Parentname', 'Angles', 'Wars'],
        iconsprite='editor/wars_ability_manager.vmt')
class EntAbilityManager(CPointEntity):
    """ Allows manipulating abilities and listens to ability completion and cancel events.
    
        Examples of manipulating abilities are:
        - Locking and unlocking abilities to prevent usage by the player
        - Hiding an ability from the player hud when locked
        - Instantly researching an ability
        - Making an ability free of costs
        
        To find the ability internal names, run the command "generate_statsabilities".
        This will generate the file "stats/statsabilities.html", listing all available abilities.
    """
    def __init__(self):
        super().__init__()
        
        abilitycanceled.connect(self.OnAbilityCanceled)
        abilitycompleted.connect(self.OnAbilityCompleted)
        
    def UpdateOnRemove(self):
        super().UpdateOnRemove()
        
        abilitycanceled.disconnect(self.OnAbilityCanceled)
        abilitycompleted.disconnect(self.OnAbilityCompleted)
        
    def OnAbilityCanceled(self, ability=None, *args, **kwargs):
        activator = ability.unit if ability.unit else self
        if not activator and ability.removedunits:
            activator = ability.removedunits[0]()
        self.abilitycanceled.Set(ability.name, activator, self)
        
    def OnAbilityCompleted(self, ability, *args, **kwargs):
        if ability.unit:
            activator = ability.unit
        elif ability.removedunits:
            activator = ability.removedunits[0]()
        else:
            activator = self
            
        self.abilitycompleted.Set(ability.name, activator, self)
        
    @input(inputname='LockAbility', helpstring='Locks the specified ability for the owner of this entity', fieldtype=fieldtypes.FIELD_STRING)
    def InputLockAbility(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputLockAbility: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputLockAbility: could not find ability %s!\n' % (abilityname))
            return
            
        technode.locked = True
        
    @input(inputname='UnlockAbility', helpstring='Unlocks the specified ability for the owner of this entity', fieldtype=fieldtypes.FIELD_STRING)
    def InputUnlockAbility(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputUnlockAbility: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputUnlockAbility: could not find ability %s!\n' % (abilityname))
            return
            
        technode.locked = False
        
    @input(inputname='HideAbilityOnUnavailabe', helpstring='Hides ability from UI if unavailable', fieldtype=fieldtypes.FIELD_STRING)
    def InputHideAbilityOnUnavailabe(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputHideAbilityOnUnavailabe: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputHideAbilityOnUnavailabe: could not find ability %s!\n' % (abilityname))
            return
            
        technode.showonunavailable = False

    @input(inputname='ShowAbilityOnUnavailabe', helpstring='Shows ability in UI even if unavailable', fieldtype=fieldtypes.FIELD_STRING)
    def InputShowAbilityOnUnavailabe(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputShowAbilityOnUnavailabe: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputShowAbilityOnUnavailabe: could not find ability %s!\n' % (abilityname))
            return
            
        technode.showonunavailable = True
        
    @input(inputname='ResearchAbility', helpstring='Researches an ability immediately. Note: some abilities may become "unresearched" again due other events.', fieldtype=fieldtypes.FIELD_STRING)
    def InputResearchAbility(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputResearchAbility: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
        
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputResearchAbility: could not find ability %s!\n' % (abilityname))
            return
            
        technode.techenabled = True

    @input(inputname='UnResearchAbility', helpstring='Unresearches an ability. Note: some abilities may become "researched" again due other events.', fieldtype=fieldtypes.FIELD_STRING)
    def InputUnResearchAbility(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputUnResearchAbility: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputUnResearchAbility: could not find ability %s!\n' % (abilityname))
            return
            
        technode.techenabled = False
        
    @input(inputname='MakeAbilityFree', helpstring='Makes the target ability free of costs (other requirements might still apply!)', fieldtype=fieldtypes.FIELD_STRING)
    def InputMakeAbilityFree(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputMakeAbilityFree: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputMakeAbilityFree: could not find ability %s!\n' % (abilityname))
            return
            
        technode.nocosts = True
        
    @input(inputname='MakeAbilityPaid', helpstring='Makes the target ability paid.', fieldtype=fieldtypes.FIELD_STRING)
    def InputMakeAbilityPaid(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputMakeAbilityPaid: no ability name specified!\n')
            return
            
        owner = self.GetOwnerNumber()
            
        technode = GetTechNode(abilityname, owner)
        if not technode:
            PrintWarning('wars_ability_manager.InputMakeAbilityPaid: could not find ability %s!\n' % (abilityname))
            return
            
        technode.nocosts = False
        
    @input(inputname='RemoveRequirements', helpstring='', fieldtype=fieldtypes.FIELD_STRING)
    def InputRemoveRequirements(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputRemoveRequirements: no ability name specified!\n')
            return

        info = GetAbilityInfo(abilityname)
        if not info:
            PrintWarning('wars_ability_manager.InputRemoveRequirements: could not find ability %s!\n' % (abilityname))
            return
            
        success, updatedvalue = ApplyAbilityAttribute(info.name, 'techrequirements', [])
        if success:
            AbilityInfoSetAttr(True, info.name, 'techrequirements', updatedvalue)
        
    @input(inputname='ResetRequirements', helpstring='', fieldtype=fieldtypes.FIELD_STRING)
    def InputResetRequirements(self, inputdata):
        abilityname = inputdata.value.String()
        if not abilityname:
            PrintWarning('wars_ability_manager.InputResetRequirements: no ability name specified!\n')
            return

        info = GetAbilityInfo(abilityname)
        if not info:
            PrintWarning('wars_ability_manager.InputResetRequirements: could not find ability %s!\n' % (abilityname))
            return
            
        f = GetField(info, 'techrequirements')
        f.Reset()
        AbilityInfoSetAttr(True, info.name, 'techrequirements', f.default)
        
    # Output fields
    abilitycompleted = OutputField(keyname='AbilityCompleted', helpstring='Fired when an ability is completed.', fieldtype=fieldtypes.FIELD_STRING)
    abilitycanceled = OutputField(keyname='AbilityCanceled', helpstring='Fired when an ability is canceled.', fieldtype=fieldtypes.FIELD_STRING)
    